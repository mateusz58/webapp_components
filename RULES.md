Claude Code Best Practices
1. Understand Before You Code
Always read entire files before making changes to avoid mistakes, duplication, or misunderstandings.
Clarify the task before starting. If anything is unclear, ask follow-up questions rather than making assumptions.
2. Work Incrementally
Break large tasks into milestones. Complete and confirm each milestone with the user before moving on.
Commit early and often to avoid losing progress if issues arise later.
3. Use Libraries Correctly
Check the latest syntax and usage for any external library unless you are 100% sure of its interface.
Never skip a library just because it seems not to work—double-check your usage and the documentation, especially if the user requested it.
4. Maintain Code Quality
Run linting after major changes to catch syntax errors and maintain code quality.
Organize code into separate files where appropriate.
Follow best practices for naming, modularity, function complexity, and file size.
Optimize for readability—code is read more often than written.
5. Implement, Don’t Mock
Never do “dummy” implementations unless explicitly asked. Always provide real, working code.
6. UI/UX Excellence
Design for aesthetics and usability. Follow UI/UX best practices, focusing on smooth, engaging, and delightful user experiences.
7. Refactoring
Avoid large refactors unless explicitly instructed.
8. Planning and Architecture
Understand the current architecture before starting a new task.
Identify files to modify and create a clear plan.
Get plan approval from the user before coding.
9. Problem Solving
Find root causes of repeated issues instead of trying random fixes or giving up.
10. Task Management
Break down large or vague tasks into smaller subtasks. If still unclear, ask the user for guidance or to help break down the task.
11. Database Understanding
Always connect to the database when working on database-related features to understand the schema structure.
Use the PostgreSQL connection string: postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database
All application tables are in the 'component_app' schema - check table structures, constraints, triggers, and functions.
Understanding database triggers and functions is crucial as they handle auto-generation of SKUs, picture names, and timestamps.
12. Project Documentation
Maintain all workflow documentation in a single PROJECT_WORKFLOW.md file organized by sections.
Never create separate files for individual features or components - always append to the existing workflow file.
Keep the workflow documentation well-organized with clear headings and subheadings for easy navigation.
Update PROJECT_WORKFLOW.md whenever analyzing new features or components to maintain a comprehensive reference.