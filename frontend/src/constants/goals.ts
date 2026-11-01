export const FIXED_GOAL_DAYS = [7, 30, 90, 180, 365] as const;
export type GoalDays = typeof FIXED_GOAL_DAYS[number];
export const GOAL_LABELS: Record<GoalDays, string> = {
  7: '7 днів', 30: '30 днів', 90: '90 днів (3 місяці)',
  180: '180 днів (пів року)', 365: '365 днів (рік)',
};
export const GOAL_DESCRIPTIONS: Record<GoalDays, string> = {
  7: 'Перший тиждень твого шляху',
  30: 'Місяць послідовності та турботи про себе',
  90: 'Дев’яносто послідовних днів',
  180: 'Сто вісімдесят послідовних днів',
  365: 'Рік щоденних кроків',
};
