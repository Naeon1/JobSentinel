/**
 * Cron 表达式与"友好配置"之间的双向转换。
 *
 * 频率类型（frequency）是一个枚举，覆盖最常见的定时需求；
 * 每种频率对应一个可读的配置参数（如时间点、N 小时间隔、星期几等）。
 * toCron 把友好配置翻译成 Cron 表达式；
 * fromCron 尝试把已存在的 Cron 反解析回友好配置（用于回填 UI）。
 */

export type Frequency =
  | 'daily'        // 每天 X 点
  | 'every_n_hours' // 每 N 小时
  | 'weekdays'     // 工作日 X 点（周一到周五）
  | 'weekly'       // 每周 X 的 Y 点
  | 'every_n_minutes' // 每 N 分钟（细粒度，少用但留作扩展）
  | 'custom'       // 高级模式：直接手填 Cron

/** 小时：0-23（两位字符串，'00'..'23'） */
export type HH = string
/** 分钟：0-59（两位字符串） */
export type MM = string

export interface ScheduleConfig {
  frequency: Frequency
  // daily / weekdays / weekly 用到的时间
  hour: HH
  minute: MM
  // every_n_hours / every_n_minutes 用到的步长
  interval: number
  // weekly 用到的星期几（0=周日,1=周一,...,6=周六；与 cron 一致）
  weekday: number
  // custom 模式直接使用
  cron_expression: string
}

/** 默认配置 */
export const defaultScheduleConfig = (): ScheduleConfig => ({
  frequency: 'daily',
  hour: '09',
  minute: '00',
  interval: 2,
  weekday: 1,
  cron_expression: '0 9 * * *',
})

const pad2 = (n: number) => String(n).padStart(2, '0')

/**
 * 把友好配置翻译成 Cron 表达式。
 * 返回 null 表示当前是 custom 模式（直接用 cron_expression 字段）。
 */
export function toCron(cfg: ScheduleConfig): string | null {
  const h = parseInt(cfg.hour, 10)
  const m = parseInt(cfg.minute, 10)
  switch (cfg.frequency) {
    case 'daily':
      return `${m} ${h} * * *`
    case 'every_n_hours': {
      const n = Math.max(1, Math.min(23, cfg.interval | 0))
      return `0 */${n} * * *`
    }
    case 'weekdays':
      return `${m} ${h} * * 1-5`
    case 'weekly':
      return `${m} ${h} * * ${cfg.weekday}`
    case 'every_n_minutes': {
      const n = Math.max(1, Math.min(59, cfg.interval | 0))
      return `*/${n} * * * *`
    }
    case 'custom':
      return cfg.cron_expression
    default:
      return null
  }
}

/** 把 Cron 反解析回友好配置；无法识别时回退到 custom 模式。 */
export function fromCron(cron: string): ScheduleConfig {
  const base = defaultScheduleConfig()
  if (!cron || !cron.trim()) return { ...base, cron_expression: cron }
  const parts = cron.trim().split(/\s+/)
  if (parts.length !== 5) {
    return { ...base, frequency: 'custom', cron_expression: cron }
  }
  const [m, h, _dom, _mon, dow] = parts

  // 工作日 X 点:  m h * * 1-5
  if (dow === '1-5' && /^\d+$/.test(m) && /^\d+$/.test(h)) {
    return {
      ...base,
      frequency: 'weekdays',
      minute: pad2(parseInt(m, 10)),
      hour: pad2(parseInt(h, 10)),
      cron_expression: cron,
    }
  }
  // 每周 X 的 Y 点:  m h * * N
  if (/^\d+$/.test(m) && /^\d+$/.test(h) && /^\d+$/.test(dow) && _dom === '*' && _mon === '*') {
    return {
      ...base,
      frequency: 'weekly',
      minute: pad2(parseInt(m, 10)),
      hour: pad2(parseInt(h, 10)),
      weekday: parseInt(dow, 10),
      cron_expression: cron,
    }
  }
  // 每天 X 点:  m h * * *
  if (/^\d+$/.test(m) && /^\d+$/.test(h) && _dom === '*' && _mon === '*' && dow === '*') {
    return {
      ...base,
      frequency: 'daily',
      minute: pad2(parseInt(m, 10)),
      hour: pad2(parseInt(h, 10)),
      cron_expression: cron,
    }
  }
  // 每 N 小时:  0 */N * * *
  if (m === '0' && /^\*\/\d+$/.test(h) && _dom === '*' && _mon === '*' && dow === '*') {
    const n = parseInt(h.slice(2), 10)
    return {
      ...base,
      frequency: 'every_n_hours',
      interval: n,
      cron_expression: cron,
    }
  }
  // 每 N 分钟:  */N * * * *
  if (/^\*\/\d+$/.test(m) && h === '*' && _dom === '*' && _mon === '*' && dow === '*') {
    const n = parseInt(m.slice(2), 10)
    return {
      ...base,
      frequency: 'every_n_minutes',
      interval: n,
      cron_expression: cron,
    }
  }
  // 其余一律归为 custom
  return { ...base, frequency: 'custom', cron_expression: cron }
}

/** 把 Cron 配置转成中文描述（用于确认展示）。 */
export function describeConfig(cfg: ScheduleConfig): string {
  const hh = cfg.hour
  const mm = cfg.minute
  switch (cfg.frequency) {
    case 'daily':
      return `每天 ${hh}:${mm} 执行`
    case 'every_n_hours':
      return `每 ${cfg.interval} 小时执行一次`
    case 'weekdays':
      return `工作日（周一至周五）${hh}:${mm} 执行`
    case 'weekly': {
      const names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
      return `每${names[cfg.weekday] ?? '周'} ${hh}:${mm} 执行`
    }
    case 'every_n_minutes':
      return `每 ${cfg.interval} 分钟执行一次`
    case 'custom':
      return `按 Cron 表达式执行：${cfg.cron_expression}`
    default:
      return ''
  }
}
