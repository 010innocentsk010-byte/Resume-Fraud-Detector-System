"""Hand-written sample resumes covering the scenarios documented in
tests/TESTING.md — a genuine/clean resume, an egregiously fabricated one, an
isolated unrealistic-education quirk, an AI-buzzword-heavy one, and a resume
designed to strongly match a specific job description. Scores were verified
by actually running each fixture through the real detector pipeline, not
computed by hand — see TESTING.md for the observed results.
"""

GENUINE_RESUME = """Jane Smith
jane.smith@example.com
+1 555-987-6543

Summary
Backend engineer with a focus on reliable, well-tested services.

Experience
Backend Engineer at Initech
Jan 2019 - Dec 2021
Built and maintained REST APIs using Python and PostgreSQL for the billing platform.

Senior Backend Engineer at Globex Corp
Jan 2022 - Present
Led the migration of legacy services to Docker and Kubernetes, improving deployment reliability.

Education
Bachelor of Science in Computer Science, 2013 - 2017

Skills
Python, PostgreSQL, Docker, Kubernetes, Git

Projects
Personal project built with Python, PostgreSQL, Docker, Kubernetes, and Git for version control.
"""

_ZWSP = "​"  # zero-width space, embedded below to simulate hidden-keyword stuffing
_LONG_LINE = "Achieved outstanding results through relentless dedication and tireless effort. " * 8
_WHITESPACE_PADDING = (
    "keywords" + ("               " * 5) + "padded" + ("               " * 5) + "text"
    + ("               " * 5) + "here" + ("               " * 5) + "again"
)

FABRICATED_RESUME = f"""Alex Morgan
alex.morgan@example.com
+1 555-111-2222

Summary
Results-driven leveraging leveraging leveraging synergy synergy synergy to streamline streamline
streamline streamline processes and facilitate facilitate facilitate facilitate innovative solutions
across a fast-paced environment with a proven track record of cutting-edge, best-in-class,
value-added, seamless, holistic{_ZWSP} excellence. Leveraging synergy to streamline and facilitate
robust, seamless, innovative solutions on a consistent and ongoing basis every single day.
{_LONG_LINE}
{_WHITESPACE_PADDING}

Experience
Chief Technology Officer at Acme Corp
Jan 2018 - Present
Oversaw all engineering initiatives.

VP of Engineering at Globex Inc
Feb 2018 - Present
Directed multiple engineering teams.

Director of Software at Initech
Mar 2018 - Present
Managed the software organization.

Head of Platform at Umbrella LLC
Apr 2018 - Present
Ran the platform division.

Engineering Lead at Hooli
May 2018 - Present
Led the engineering department.

Education
Bachelor of Arts in Business, 2015 - 2015

PhD in Computer Science, 2016 - 2016

Master of Science in Data Science, 2018 - 2020

Bachelor of Science in Computer Science, 2019 - 2021

Skills
Kubernetes, AWS, Terraform, GraphQL, Rust, Go, TensorFlow, PyTorch, Azure, GCP, Machine Learning,
Deep Learning, Microservices, Docker, Python, Java, JavaScript, TypeScript, C++, C#, Ruby, PHP,
Swift, Kotlin, SQL, MongoDB
"""

UNREALISTIC_EDUCATION_RESUME = """Sam Rivera
sam.rivera@example.com
+1 555-333-4444

Summary
Software developer.

Experience
Software Developer at Wayne Enterprises
Jun 2021 - Present
Worked on internal tooling using Python.

Education
Bachelor of Science in Computer Science, 2020 - 2021

Skills
Python, SQL
"""

AI_BUZZWORD_RESUME = """Taylor Reed
taylor.reed@example.com
+1 555-777-8888

Summary
Results-driven, detail-oriented professional leveraging cutting-edge, innovative solutions in a
fast-paced environment. Highly motivated self-starter with a proven track record of leveraging
synergy to streamline operations. Passionate about utilizing best-in-class strategies to
facilitate seamless, robust, value-added outcomes for every stakeholder involved. Utilized a wide
range of in-depth knowledge to leverage synergy for a holistic approach to every single project.
Leveraged extensive experience and excellent communication skills to facilitate robust, seamless,
cutting-edge solutions across every fast-paced environment encountered. Utilized proven track
record of streamlined, value-added, best-in-class synergy on a consistent and ongoing basis daily.
Leveraged innovative solutions with a results-driven, detail-oriented, holistic approach overall.

Experience
Software Engineer at Acme Corp
Jan 2020 - Present
Leveraged synergy to facilitate robust solutions.

Education
Bachelor of Science in Computer Science, 2014 - 2018

Skills
Python, SQL
"""

STRONG_MATCH_RESUME = """Jordan Lee
jordan.lee@example.com
+1 555-999-0000

Summary
Senior backend engineer specializing in distributed systems.

Experience
Senior Backend Engineer at CloudScale Inc
Jan 2019 - Present
Built and scaled backend services using Python, Docker, and Kubernetes on AWS. Managed PostgreSQL
databases and CI/CD pipelines, and mentored junior engineers on system design.

Backend Engineer at DataForge
Jun 2016 - Dec 2018
Developed REST APIs and GraphQL services using Python and PostgreSQL.

Education
Bachelor of Science in Computer Science, 2012 - 2016

Skills
Python, Docker, Kubernetes, AWS, PostgreSQL, GraphQL, CI/CD, Git
"""

SAMPLE_JOB_DESCRIPTION = """We are looking for a Senior Backend Engineer to join our growing engineering team.

Requirements:
- 5+ years of experience with Python, Docker, and Kubernetes
- Strong experience with AWS and PostgreSQL
- Familiarity with GraphQL and CI/CD pipelines
- Experience mentoring junior engineers and leading technical design reviews
"""

UNRELATED_JOB_DESCRIPTION = """We are looking for a Registered Nurse to join our hospital's emergency department.

Requirements:
- Active RN license and BLS/ACLS certification
- 3+ years of emergency or critical care nursing experience
- Strong patient triage and clinical assessment skills
- Ability to work rotating 12-hour shifts
"""
