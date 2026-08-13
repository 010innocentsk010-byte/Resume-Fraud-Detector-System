import type {
  Analysis,
  Applicant,
  CandidateRankingEntry,
  DashboardAnalytics,
  DashboardSummary,
  JobDescription,
  JobMatch,
  ReportRead,
  ResumeDetail,
  RewriteSuggestionsRead,
  TokenPair,
  User,
  UserRole,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "rfds_access_token";
const REFRESH_TOKEN_KEY = "rfds_refresh_token";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export const tokenStorage = {
  get access(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  get refresh(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  set(tokens: TokenPair) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  },
  clear() {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ") || res.statusText;
    }
    return res.statusText;
  } catch {
    return res.statusText;
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = tokenStorage.refresh;
  if (!refresh) return false;
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  const tokens: TokenPair = await res.json();
  tokenStorage.set(tokens);
  return true;
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Body is already a fetch-ready BodyInit (FormData, url-encoded string, ...) — send as-is, skip JSON.stringify and the default JSON content-type. */
  raw?: boolean;
  skipAuth?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}, retried = false): Promise<T> {
  const { body, raw, skipAuth, headers, ...rest } = options;

  const finalHeaders = new Headers(headers);
  if (!raw && body !== undefined) {
    finalHeaders.set("Content-Type", "application/json");
  }
  if (!skipAuth) {
    const token = tokenStorage.access;
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: body === undefined ? undefined : raw ? (body as BodyInit) : JSON.stringify(body),
  });

  if (res.status === 401 && !skipAuth && !retried) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return request<T>(path, options, true);
    }
    tokenStorage.clear();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!res.ok) {
    throw new ApiError(res.status, await extractErrorMessage(res));
  }

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return undefined as T;
}

export const authApi = {
  async login(email: string, password: string): Promise<TokenPair> {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return request<TokenPair>("/auth/login", {
      method: "POST",
      skipAuth: true,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
      raw: true,
    });
  },
  register(payload: { name: string; email: string; password: string; organization?: string; role?: UserRole }) {
    return request<User>("/auth/register", { method: "POST", skipAuth: true, body: payload });
  },
  logout(refreshToken: string) {
    return request<void>("/auth/logout", {
      method: "POST",
      skipAuth: true,
      body: { refresh_token: refreshToken },
    });
  },
};

export const applicantsApi = {
  list(q?: string) {
    const query = q ? `?q=${encodeURIComponent(q)}` : "";
    return request<Applicant[]>(`/applicants${query}`);
  },
  get(id: string) {
    return request<Applicant>(`/applicants/${id}`);
  },
  create(payload: { name: string; email: string; phone?: string; field_of_study?: string }) {
    return request<Applicant>("/applicants", { method: "POST", body: payload });
  },
  remove(id: string) {
    return request<void>(`/applicants/${id}`, { method: "DELETE" });
  },
};

export const resumesApi = {
  listForApplicant(applicantId: string) {
    return request<ResumeDetail[]>(`/applicants/${applicantId}/resumes`);
  },
  get(resumeId: string) {
    return request<ResumeDetail>(`/resumes/${resumeId}`);
  },
  upload(applicantId: string, file: File) {
    const form = new FormData();
    form.append("file", file);
    return request<ResumeDetail>(`/applicants/${applicantId}/resumes`, {
      method: "POST",
      raw: true,
      body: form,
    });
  },
  analyze(resumeId: string) {
    return request<Analysis>(`/resumes/${resumeId}/analyze`, { method: "POST" });
  },
  getLatestAnalysis(resumeId: string) {
    return request<Analysis>(`/resumes/${resumeId}/analysis`);
  },
};

export const analysisApi = {
  get(analysisId: string) {
    return request<Analysis>(`/analysis/${analysisId}`);
  },
};

export const reportsApi = {
  get(analysisId: string) {
    return request<ReportRead>(`/reports/${analysisId}`);
  },
  async downloadPdf(analysisId: string): Promise<Blob> {
    const token = tokenStorage.access;
    const res = await fetch(`${API_URL}/reports/${analysisId}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!res.ok) throw new ApiError(res.status, await extractErrorMessage(res));
    return res.blob();
  },
};

export const dashboardApi = {
  summary() {
    return request<DashboardSummary>("/dashboard/summary");
  },
  analytics() {
    return request<DashboardAnalytics>("/dashboard/analytics");
  },
};

export const rewriteApi = {
  generate(resumeId: string) {
    return request<RewriteSuggestionsRead>(`/resumes/${resumeId}/rewrite-suggestions`, { method: "POST" });
  },
};

export const jobMatchApi = {
  listJobDescriptions(q?: string) {
    const query = q ? `?q=${encodeURIComponent(q)}` : "";
    return request<JobDescription[]>(`/job-descriptions${query}`);
  },
  createJobDescription(payload: { title: string; company?: string; career_field?: string; raw_text: string }) {
    return request<JobDescription>("/job-descriptions", { method: "POST", body: payload });
  },
  match(
    resumeId: string,
    payload: {
      job_description_id?: string;
      job_description_text?: string;
      title?: string;
      company?: string;
      career_field?: string;
    }
  ) {
    return request<JobMatch>(`/resumes/${resumeId}/job-match`, { method: "POST", body: payload });
  },
  listMatchesForResume(resumeId: string) {
    return request<JobMatch[]>(`/resumes/${resumeId}/job-matches`);
  },
  rankCandidates(jobDescriptionId: string) {
    return request<CandidateRankingEntry[]>(`/job-descriptions/${jobDescriptionId}/candidate-ranking`);
  },
};

export const adminApi = {
  listUsers() {
    return request<User[]>("/admin/users");
  },
  updateUser(userId: string, payload: { role?: UserRole; is_active?: boolean }) {
    return request<User>(`/admin/users/${userId}`, { method: "PATCH", body: payload });
  },
};
