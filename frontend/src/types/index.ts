// User types
export interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  is_active: boolean;
  is_verified?: boolean;
  created_at?: string;
  last_login_at?: string;
  has_profile?: boolean;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
}

// Profile types
export interface Experience {
  title: string;
  company: string;
  start_date: string;
  end_date?: string;
  location?: string;
  description?: string;
  // Legacy fields for compatibility
  poste?: string;
  entreprise?: string;
  dates?: string;
  competences?: string[];
}

export interface Education {
  diplome: string;
  ecole: string;
  annee?: string;
  lieu?: string;
}

export interface Language {
  language: string;
  level: string;
}

export interface UserProfile {
  id: number;
  user_id: number;
  cv_file_path?: string;
  user_description?: string;
  ai_description?: string;
  ai_generated_summary?: string;
  title?: string;
  summary?: string;
  experiences?: Experience[];
  skills?: string[];
  languages?: string[];
  education?: Education[];
  latest_job_title?: string;
  years_of_experience?: number;
  preferred_location?: string;
  created_at?: string;
  updated_at?: string;
  cv_analyzed_at?: string;
}

// Scoring Criteria types
export interface SubCriteriaOption {
  name: string;
  enabled: boolean;
  importance: number;
}

export interface SubCriteria {
  options?: SubCriteriaOption[];
  custom?: SubCriteriaOption[];
  value?: string;
  max_distance?: number;
  min_value?: number;
  currency?: string;
}

export interface ScoringCriteria {
  id: string;
  name: string;
  criteria_type?: string;
  enabled: boolean;
  importance: number;
  sub_criteria?: SubCriteria;
  created_at?: string;
  updated_at?: string;
}

export type CriteriaType = 
  | 'job_title'
  | 'location'
  | 'contract_type'
  | 'salary'
  | 'work_mode'
  | 'company_size'
  | 'seniority'
  | 'values'
  | 'languages'
  | 'skills';

// Job types
export interface Company {
  id: number;
  name: string;
  description?: string;
  website?: string;
  logo_url?: string;
  headquarters?: string;
  industry?: string;
  company_size?: string;
  rating?: number;
}

export interface Job {
  id: number;
  title: string;
  description?: string;
  requirements?: string;
  location?: string;
  remote_type?: string;
  remote?: boolean;
  contract_type?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  job_type?: string;
  experience_level?: string;
  url?: string;
  source_url?: string;
  source_platform?: string;
  skills?: string[];
  benefits?: string[];
  company_id?: number;
  company?: string;
  company_data?: Company;
  is_active?: boolean;
  posted_date?: string;
  created_at?: string;
}

export interface ScoredJob extends Job {
  score: number;
  score_breakdown?: Record<string, number>;
}

// Blacklist types
export interface BlacklistEntry {
  id: string;
  company_name: string;
  company_id?: number;
  reason?: string;
  created_at: string;
}

// Application types
export type ApplicationStatus = 
  | 'saved'
  | 'applied'
  | 'phone_screen'
  | 'interview'
  | 'technical'
  | 'final_round'
  | 'offer'
  | 'rejected'
  | 'withdrawn';

export interface Application {
  id: number;
  job_id: number;
  job?: Job;
  status: ApplicationStatus;
  cover_letter?: string;
  notes?: string;
  next_action?: string;
  next_action_date?: string;
  applied_at?: string;
  created_at?: string;
}
