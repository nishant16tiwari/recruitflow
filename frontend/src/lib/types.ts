export type UserRole = 'RECRUITER' | 'INTERVIEWER'

export type Stage = 'Applied' | 'Screening' | 'Interview' | 'Offer' | 'Hired' | 'Rejected'

export const PIPELINE_STAGES: Stage[] = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired']

export interface User {
  id: number
  email: string
  name: string
  role: UserRole
}

export type JobStatus = 'OPEN' | 'ARCHIVED'

export interface Job {
  id: number
  title: string
  department: string
  description: string
  status: JobStatus
  created_by: number
  created_at: string
  updated_at: string
}

export interface JobWithCount extends Job {
  application_count: number
}

export interface Application {
  id: number
  job_id: number
  candidate_name: string
  candidate_email: string
  source: string
  notes: string
  applied_date: string
  current_stage: Stage
  previous_stage_before_rejection: Stage | null
  stage_entered_at: string
  created_by: number
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export type HistoryEventType =
  | 'CREATED'
  | 'STAGE_CHANGE'
  | 'REJECTED'
  | 'REINSTATED'
  | 'FEEDBACK'
  | 'INTERVIEW_SCHEDULED'
  | 'INTERVIEWER_ASSIGNED'
  | 'INTERVIEWER_REMOVED'

export interface HistoryEvent {
  id: number
  application_id: number
  event_type: HistoryEventType
  from_stage: Stage | null
  to_stage: Stage | null
  actor_id: number
  note: string
  created_at: string
}

export interface PanelMember {
  id: number
  application_id: number
  interviewer_id: number
  assigned_at: string
  interviewer: User
}

export interface Feedback {
  id: number
  application_id: number
  interviewer_id: number
  content: string
  created_at: string
}

export interface Interview {
  id: number
  application_id: number
  date: string
  start_time: string
  end_time: string
  interview_type: string
  location: string | null
  meeting_link: string | null
  created_by: number
  created_at: string
  interviewers: User[]
}

export interface BulkActionResult {
  application_id: number
  success: boolean
  old_stage: Stage | null
  new_stage: Stage | null
  reason: string | null
}

export interface DashboardData {
  open_positions: number
  active_applications: number
  interviews_this_week: number
  hires_this_month: number
  by_job_opening: { job_id: number; job_title: string; count: number }[]
  by_stage: { stage: string; count: number }[]
  weekly_applications: { week_start: string; count: number }[]
}

export interface AlertItem {
  application_id: number
  candidate_name: string
  job_id: number
  job_title: string
  current_stage: Stage
  stage_entered_at: string
  days_in_stage: number
}
