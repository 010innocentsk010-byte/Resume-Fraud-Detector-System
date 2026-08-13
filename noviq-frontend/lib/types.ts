export type UserRole = "admin" | "recruiter";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  organization: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Applicant {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  field_of_study: string | null;
  created_at: string;
  resume_count: number;
  latest_fraud_score: number | null;
  latest_risk_level: RiskLevel | null;
  latest_flag_count: number | null;
}

export type ResumeFileType = "pdf" | "docx";
export type ResumeStatus = "uploaded" | "parsing" | "parsed" | "analyzing" | "analyzed" | "failed";

export interface ParsedContact {
  name: string | null;
  email: string | null;
  phone: string | null;
}

export interface ParsedEducationEntry {
  degree: string | null;
  field: string | null;
  institution: string | null;
  start_year: number | null;
  end_year: number | null;
  raw_text: string;
}

export interface ParsedExperienceEntry {
  title: string | null;
  company: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  raw_text: string;
}

export interface ParsedResume {
  contact: ParsedContact;
  skills: string[];
  education: ParsedEducationEntry[];
  experience: ParsedExperienceEntry[];
  certifications: string[];
  projects: string[];
  sections_found: string[];
}

export interface Resume {
  id: string;
  applicant_id: string;
  original_filename: string;
  file_type: ResumeFileType;
  file_size_bytes: number;
  status: ResumeStatus;
  created_at: string;
}

export interface ResumeDetail extends Resume {
  parsed_data: ParsedResume | null;
}

export type RiskLevel = "low" | "medium" | "high";
export type FlagSeverity = "low" | "medium" | "high";

export interface FraudFlag {
  category: string;
  severity: FlagSeverity;
  title: string;
  message: string;
  evidence: string[];
}

export interface SectionAIScore {
  section: string;
  ai_confidence: number;
  signals: string[];
}

export interface ConsistencyCheck {
  category: string;
  label: string;
  passed: boolean;
}

export interface Analysis {
  id: string;
  resume_id: string;
  experience_score: number;
  education_score: number;
  skill_score: number;
  formatting_score: number;
  timeline_score: number;
  ai_score: number;
  keyword_stuffing_score: number;
  duplicate_score: number;
  fraud_score: number;
  risk_level: RiskLevel;
  flags: FraudFlag[];
  details: Record<string, unknown>;
  ats_score: number;
  ats_issues: FraudFlag[];
  ai_section_scores: SectionAIScore[];
  consistency_checks: ConsistencyCheck[];
  created_at: string;
}

export interface BulletRewriteSuggestion {
  original: string;
  rewritten: string;
  rationale: string;
}

export interface RewriteSuggestionsRead {
  resume_id: string;
  suggestions: BulletRewriteSuggestion[];
  model: string;
  generated_at: string;
}

export interface JobDescription {
  id: string;
  title: string;
  company: string | null;
  career_field: string | null;
  raw_text: string;
  parsed_skills: string[];
  created_at: string;
}

export interface JobMatch {
  id: string;
  resume_id: string;
  job_description_id: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  semantic_similarity: number;
  recommendation: string;
  details: Record<string, unknown>;
  created_at: string;
  job_description: JobDescription | null;
}

export interface CandidateRankingEntry {
  applicant_id: string;
  applicant_name: string;
  applicant_email: string;
  resume_id: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  recommendation: string;
  fraud_score: number | null;
  risk_level: RiskLevel | null;
  ats_score: number | null;
}

export interface ReportRead {
  id: string;
  analysis_id: string;
  recommendation: string;
  created_at: string;
}

export interface DashboardSummary {
  total_applicants: number;
  total_resumes: number;
  verified_candidates: number;
  high_risk_candidates: number;
  medium_risk_candidates: number;
  low_risk_candidates: number;
  ai_detection_rate: number;
  average_fraud_score: number;
}

export interface RiskDistributionPoint {
  label: string;
  count: number;
}

export interface TrendPoint {
  date: string;
  average_fraud_score: number;
  count: number;
}

export interface FlagCategoryCount {
  category: string;
  count: number;
}

export interface DashboardAnalytics {
  summary: DashboardSummary;
  risk_distribution: RiskDistributionPoint[];
  fraud_trend: TrendPoint[];
  top_flag_categories: FlagCategoryCount[];
}
