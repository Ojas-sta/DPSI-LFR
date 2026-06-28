# 12 Prompts

## Purpose

The Prompts folder is a curated library of AI prompts used across the project — for code generation, code review, documentation, testing, debugging, and analysis. Centralizing prompts ensures consistency, enables reuse, and makes it possible to iterate on prompt effectiveness over time.

## Contents

| Item | Type | Description |
|------|------|-------------|
| `PRM-NNN-<Category>-<Title>.md` | Prompt | Individual prompt with metadata and usage notes |
| `PromptIndex.md` | Index | Categorized index of all prompts |
| `PromptEngineeringGuide.md` | Guide | Best practices for writing and testing prompts |
| `README.md` | Guide | This file |

## Workflow

1. **Prompt Creation**: When a reusable prompt is identified, create a `PRM-NNN-<Category>-<Title>.md`.
2. **Testing**: Test prompts against sample inputs and document expected outputs.
3. **Iteration**: Refine prompts based on results — update the file and note changes.
4. **Categorization**: Assign each prompt to a category: `codegen`, `review`, `docs`, `test`, `debug`, `analysis`.
5. **Indexing**: Add to `PromptIndex.md` under the appropriate category.
6. **Usage Tracking**: Note when and where each prompt is used to track effectiveness.

## Conventions

- Prompt filenames: `PRM-NNN-Category-Short-Title.md`.
- Each prompt includes: `Category`, `Purpose`, `System Prompt`, `User Template`, `Variables`, `Example Output`, `Notes`.
- Variables in templates use `{{variable_name}}` syntax.
- System prompts are included in full — no external references.
- Rate prompt effectiveness: `⭐⭐⭐⭐⭐` (1-5 stars).
- Tag prompts with `<!-- model: gpt-4 | claude | gemini | all -->`.

## Examples

```markdown
## PRM-001-codegen-component.md excerpt

## Category
codegen

## Purpose
Generate a React functional component with TypeScript.

## System Prompt
You are an expert React developer. Generate clean, accessible,
TypeScript-typed components following the project's coding standards.

## User Template
Create a {{componentType}} component named {{componentName}}
that {{description}}. Use {{styling}} for styling.

## Variables
| Variable | Description | Example |
|----------|-------------|---------|
| componentType | Type of component | form, table, modal |
| componentName | PascalCase name | UserForm |
| description | What it does | displays user profile |
| styling | Styling approach | Tailwind, CSS Modules |
```
