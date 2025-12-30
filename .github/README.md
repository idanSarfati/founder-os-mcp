# GitHub Action Guard (CI/CD)

A GitHub Action that validates pull request changes against business requirements stored in Notion, linked via Linear issues.

## 🚀 How It Works

1. **Trigger**: Runs on every pull request (opened, synchronize, reopened)
2. **Parse PR Title**: Extracts Linear issue ID from PR title format `[ISSUE-ID]`
3. **Fetch Requirements**: Queries Linear API to find linked Notion page with specifications
4. **Validate Changes**: Uses LLM (Gemini) to compare git diff against Notion spec
5. **Block/Fail**: Fails the build if violations are detected and posts detailed comment

## 📋 Prerequisites

### Required Secrets
Add these secrets to your GitHub repository:

- `NOTION_TOKEN`: Your Notion API token
- `LINEAR_API_KEY`: Your Linear API key
- `GEMINI_API_KEY`: Google Gemini API key for LLM validation

### PR Title Format
Pull request titles must include the Linear issue ID in brackets:
```
feat: implement user login [ENG-5]
fix: button color validation [FOS-101]
```

### Linear Issue Setup
The Linear issue description must contain a link to the Notion page with requirements:
```
This feature requires the login button to be purple.
See spec: https://www.notion.so/Feature-Login-Button-2d76a23768e68019b979e9e55ce505fe
```

## 🔧 Setup

1. Copy the workflow file to your repository:
   ```bash
   cp .github/workflows/action-guard.yml your-repo/.github/workflows/
   cp .github/scripts/action-guard.py your-repo/.github/scripts/
   ```

2. Add the required secrets to your GitHub repository settings.

3. The action will automatically run on all pull requests.

## 🎯 Example Usage

### ✅ Compliant PR
- **Title**: `feat: update button color to purple [ENG-5]`
- **Linked Issue**: ENG-5 with Notion spec requiring "purple" color
- **Changes**: CSS updated to `color: purple`
- **Result**: ✅ Build passes

### ❌ Non-Compliant PR
- **Title**: `feat: update button color to blue [ENG-5]`
- **Linked Issue**: ENG-5 with Notion spec requiring "purple" color
- **Changes**: CSS updated to `color: blue`
- **Result**: 🚫 Build fails with detailed violation comment

## 🛠️ Technical Details

### Dependencies
- Python 3.9+
- `requests` for API calls
- `google-generativeai` for LLM validation

### API Calls
1. **GitHub API**: Get PR details (title, number)
2. **Linear API**: Fetch issue details and find Notion link
3. **Notion API**: Retrieve specification content
4. **Gemini API**: Validate changes against requirements

### Error Handling
- Missing secrets: Immediate failure
- Invalid PR title format: Failure with guidance
- API failures: Logged errors, defaults to allowing changes
- LLM failures: Defaults to allowing changes

## 📊 Validation Logic

The LLM validation uses this prompt structure:

```
SPECIFICATION: [Notion page content]

CODE CHANGES: [Git diff]

TASK: Analyze the code changes and determine if they violate any requirements in the specification.

Respond with ONLY "YES" if the changes violate the spec, or "NO" if they comply.
If violations are found, briefly explain why.
```

## 🔍 Debugging

Check the action logs for detailed output:
- ✅ Success messages for compliant changes
- 🚫 Violation details for non-compliant changes
- ❌ Error messages for API or parsing failures

## 🤝 Contributing

This is a Proof of Concept implementation. Future enhancements:
- Support for multiple LLM providers
- Enhanced Notion content parsing
- Configurable validation rules
- Integration with other requirement management tools
