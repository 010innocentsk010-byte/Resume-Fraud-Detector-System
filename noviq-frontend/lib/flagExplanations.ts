import type { FraudFlag } from "./types";

/**
 * Plain-language explanations of what each fraud-detection flag actually
 * means, shown in the "explain this flag" popover. Keyed by the flag's
 * exact title (set server-side in noviq-backend/app/services/fraud/*.py).
 */
const EXPLANATIONS_BY_TITLE: Record<string, string> = {
  // formatting
  "Hidden/invisible characters detected":
    "The system found invisible characters hidden in the document text — a trick sometimes used to stuff extra keywords that only automated scanners can see, not human readers.",
  "Unusual control characters":
    "The system found non-standard characters embedded in the text that don't normally appear in a clean document, which can be a sign of a manipulated or poorly-converted file.",
  "No clear resume structure detected":
    "The system looked for standard section headers like Experience, Education, and Skills but couldn't find them, which can happen with unusual templates or resumes scanned as images.",
  "Abnormally long text lines":
    "The system found lines of text far longer than normal, usually meaning the layout (like tables or columns) didn't convert cleanly into readable text.",
  "Excessive whitespace padding":
    "The system found large gaps of blank space in the text, which is sometimes used to hide extra keywords off-screen.",

  // ai_generated
  "High density of generic/AI-style phrasing":
    "The system noticed the text is packed with generic corporate buzzwords that AI writing tools tend to overuse, more than what's typical in natural writing.",
  "Unusually uniform sentence structure":
    "The system noticed that almost every sentence is nearly the same length, a pattern that's more common in AI-generated text than in natural human writing.",
  "Repetitive sentence openers":
    "The system noticed a pattern where multiple bullet points or sentences begin with the exact same word, suggesting the text may have been templated or auto-generated.",
  "Repeated phrase templates":
    "The system found the same short phrase structure repeated across multiple bullet points, which can indicate templated or auto-generated content rather than original writing.",

  // keyword_stuffing
  "Keyword stuffing detected":
    "The system noticed certain words appearing far more often than natural writing would use them, a common tactic to game automated keyword scanners.",
  "Repeated consecutive keywords":
    "The system found the same word repeated back-to-back multiple times, which is unusual for normal writing and often a sign of deliberate keyword stuffing.",

  // duplicate
  "Exact duplicate resume text":
    "The system found that this resume's text is essentially identical to one that was already submitted before.",
  "Likely duplicate submission":
    "The system compared this resume's meaning (not just exact words) to previous submissions and found it extremely similar to one already on file.",
  "Similar to a previous submission":
    "The system found this resume noticeably similar in content to a previous submission, which could mean a reused template or a resubmission.",

  // timeline
  "Invalid employment date range":
    "The system noticed a job listed with an end date that comes before its start date, which isn't possible.",
  "Overlapping employment periods":
    "The system noticed two jobs listed with dates that overlap by a year or more, which is unusual for two full-time roles.",
  "Possible timeline inconsistency":
    "The system noticed a job's dates overlap significantly with a period of full-time education, which is worth double-checking unless the role was part-time.",
  "Rapid job-hopping pattern":
    "The system noticed an unusually high number of jobs packed into a short span of time.",

  // education
  "Invalid education date range":
    "The system noticed an education entry with an end date that comes before its start date, which isn't possible.",
  "Unrealistic program duration":
    "The system noticed a degree listed with a duration far shorter than that type of program normally takes to complete full-time.",
  "Overlapping full-time degree programs":
    "The system noticed two full-time degree programs listed with dates that overlap by a year or more, which is unusual.",
  "Education dates missing":
    "The system couldn't find verifiable start or end years for any of the education entries listed.",

  // skills
  "Possible skill exaggeration":
    "The system checked whether each listed skill is backed up anywhere in the experience or project descriptions, and found that most of them aren't mentioned again — a possible sign of exaggeration.",
  "Some claimed skills lack supporting evidence":
    "The system checked the listed skills against the rest of the resume and found a notable number that are never mentioned again in any job or project description.",
  "Advanced/specialist skills without evidence":
    "The system noticed several advanced, specialist technologies listed that never come up again in any project or role description, which is unusual for skills someone actually has hands-on experience with.",
  "Unusually large skill list":
    "The system noticed an unusually long list of claimed skills, which can sometimes indicate keyword stuffing rather than genuine, focused expertise.",

  // ats
  "No extractable text":
    "No text could be extracted from this document at all — an ATS would see a completely blank resume.",
  "Missing contact email":
    "No email address was detected. ATS systems and recruiters rely on a clearly extractable email address to route and contact candidates.",
  "Missing contact phone number":
    "No phone number was detected in the document text.",
  "Few standard section headers detected":
    "Standard section headers like Experience, Education, and Skills could not be reliably identified, which can cause an ATS parser to drop or misclassify content.",
  "Hidden characters may break ATS parsing":
    "Zero-width or invisible unicode characters were found, which can corrupt keyword matching and text extraction in ATS parsers.",
  "Resume content is unusually brief":
    "Very little extractable text was found — often a sign the ATS parser is missing content (e.g. text embedded in an image) rather than a genuinely brief resume.",
  "Complex layout may not parse cleanly (tables/columns)":
    "Abnormally long lines were found in the extracted text, often a sign of multi-column layouts or tables that ATS parsers read out of order or merge together.",
  "No recognizable skills section found":
    "No recognizable skills were detected. Many ATS systems rank candidates heavily on keyword/skill matches, so an explicit skills section improves match rates.",
};

const EXPLANATIONS_BY_CATEGORY: Record<string, string> = {
  formatting: "The system found something unusual in how the document is structured or encoded.",
  ai_generated: "The system noticed a writing pattern more common in AI-generated text than natural human writing.",
  keyword_stuffing: "The system noticed word repetition patterns commonly used to game automated keyword scanners.",
  duplicate: "The system found this resume closely matches one that was already submitted before.",
  timeline: "The system found an inconsistency in the dates reported for this candidate's history.",
  education: "The system found an inconsistency in the education history reported.",
  skills: "The system found a discrepancy between the skills claimed and what's backed up elsewhere in the resume.",
  ats: "The system found something that could prevent an Applicant Tracking System from parsing this resume correctly.",
};

export function explainFlag(flag: FraudFlag): string {
  return EXPLANATIONS_BY_TITLE[flag.title] ?? EXPLANATIONS_BY_CATEGORY[flag.category] ?? flag.message;
}
