import { apiRequest } from './client';
export type StatisticsPeriod = 'all' | 'week' | 'month' | 'year';
export type Statistics = {
  sober_days: number;
  relapse_days: number;
  period_start: string;
  period_end: string;
  total_sober_days: number;
  current_streak: number;
  longest_streak: number;
  active_goal_days: number | null;
  completed_goal_days: number[];
  goal_progress_days: number;
  has_goals: boolean;
};
export const getStatistics = (period: StatisticsPeriod): Promise<Statistics> =>
  apiRequest(`/statistics?period=${period}`);
