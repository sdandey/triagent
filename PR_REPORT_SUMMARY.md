# Pull Request Report Summary - Omnia Data Teams

## Report Details

- **Organization**: symphonyvsts
- **Project**: Audit Cortex 2
- **Date Range**: June 27, 2025 - December 24, 2025 (6 months)
- **Report Generated**: December 24, 2025
- **Report Location**: `/Users/sdandey/Documents/code/triagent/pr_report_20251224.html`

## Executive Summary

### Overall Statistics
- **Total PRs Analyzed**: 730 PRs (in date range)
- **Total PRs Fetched**: 3,070 PRs (across all time)
- **Repositories Analyzed**: 18 repositories
- **Teams Tracked**: 20 teams across 5 PODs

### Repository Coverage
The report includes PRs from the following repositories targeting `develop`, `master`, or `main` branches:

1. data-exchange-service
2. cortex-datamanagement-services
3. engagement-service
4. security-service
5. data-kitchen-service
6. analytic-template-service
7. notification-service
8. staging-service
9. spark-job-management
10. cortex-ui
11. client-service
12. workpaper-service
13. async-workflow-framework
14. sampling-service
15. localization-service
16. scheduler-service
17. cortexpy
18. analytic-notebooks

## Team Organization

### Data Acquisition and Preparation POD
- **Alpha**: Audit Cortex 2\Omnia Data\Omnia Data Management\Data Acquisition and Preparation\Alpha
- **Beta**: Audit Cortex 2\Omnia Data\Omnia Data Management\Data Acquisition and Preparation\Beta
- **Megatron**: Audit Cortex 2\Omnia Data\Omnia Data Management\Data Acquisition and Preparation\Megatron

### Data Management and Activation POD
- **Delta**: Audit Cortex 2\Omnia Data\Omnia Data Management\Data Management and Activation\Delta
- **Gamma**: Audit Cortex 2\Omnia Data\Omnia Data Management\Data Management and Activation\Gamma
- **Skyrockets**: Audit Cortex 2\Omnia Data\Omnia Data Management\Data Management and Activation\Skyrockets

### Omnia JE POD
- **Exa**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Exa
- **Jupiter**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Jupiter
- **Justice League**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Justice League
- **Neptune**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Neptune
- **Peta**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Peta
- **Saturn**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Saturn
- **Utopia**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Omnia JE\Utopia

### Data In Use POD
- **Giga**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Giga
- **Kilo**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Kilo
- **Tera**: Audit Cortex 2\Omnia Data\Omnia Data Automation\Data In Use\Tera

### Other Teams
- **Galileo**: Audit Cortex 2\Omnia Data\Omnia Data Acquisition\Galileo
- **Core Data Engineering**: Audit Cortex 2\Omnia Data\Core Data Engineering
- **Health Monitoring**: Audit Cortex 2\Omnia Data\Health Monitoring
- **SpaceBots**: Audit Cortex 2\Omnia Data\SpaceBots

## Report Features

The HTML report includes:

1. **Executive Dashboard**
   - Total PRs created and merged
   - Overall merge rate
   - Number of active teams

2. **Daily Activity Charts**
   - Interactive line charts showing PR creation trends
   - PR merge trends over time
   - Built with Chart.js for dynamic visualization

3. **Team Summary Table**
   - PRs by team
   - Merge rates per team
   - Sortable and filterable views

4. **Detailed POD Sections**
   - PRs grouped by organizational PODs
   - Individual team breakdowns
   - Up to 50 most recent PRs per team
   - Clickable PR links to Azure DevOps

5. **PR Details**
   - PR ID with direct links to Azure DevOps
   - Title and description
   - Author information
   - Repository name
   - Creation date
   - Status (completed/active)

## How to View the Report

1. **Open in Browser**
   ```bash
   open /Users/sdandey/Documents/code/triagent/pr_report_20251224.html
   ```

2. **View in Any Browser**
   - Navigate to: `/Users/sdandey/Documents/code/triagent/pr_report_20251224.html`
   - The report is a standalone HTML file with no external dependencies (except Chart.js CDN)

## Methodology

### Data Collection
1. **Azure DevOps CLI**: Used `az repos pr list` command to fetch PRs from each repository
2. **Filtering**: PRs were filtered by:
   - Target branches: develop, master, main
   - Creation date: June 27, 2025 - December 24, 2025
   - Status: All (active, completed, abandoned)

### Team Assignment
PRs were assigned to teams using the following logic:
1. **Primary Method**: Query linked work items via `az boards work-item show`
2. **Area Path Matching**: Extract `System.AreaPath` from work items and match to team definitions
3. **Fallback**: PRs without work items or unmatched area paths are categorized as "Unknown"

### Metrics Calculated
- **Total PRs**: Count of PRs created in date range
- **Merged PRs**: Count of PRs with status = "completed"
- **Merge Rate**: (Merged PRs / Total PRs) × 100
- **Daily Created**: Count of PRs created per day
- **Daily Merged**: Count of PRs merged per day

## Limitations

1. **Work Item Dependency**: Team assignment relies on PRs having linked work items with proper area paths
2. **API Limits**: Azure DevOps CLI returns maximum 101 PRs per query
3. **Unknown Teams**: PRs without work items or with non-matching area paths are categorized as "Unknown"
4. **Rate Limiting**: Work item queries are performed individually, which may be slow for large datasets

## Future Enhancements

Potential improvements for future versions:
1. Add repository-level breakdowns
2. Include PR size metrics (lines changed)
3. Add review time statistics
4. Include PR approval metrics
5. Add team velocity trends
6. Export to Excel/CSV formats
7. Add filtering and search capabilities
8. Include pipeline success rates

## Script Location

The report generator script is available at:
```
/Users/sdandey/Documents/code/triagent/pr_report_generator.py
```

### Running the Script
```bash
python3 /Users/sdandey/Documents/code/triagent/pr_report_generator.py
```

### Requirements
- Python 3.7+
- Azure CLI (`az`) installed and configured
- Authenticated with Azure DevOps (via `az login` or PAT)
- Access to symphonyvsts organization and Audit Cortex 2 project

## Technical Details

### Technologies Used
- **Python 3**: Core scripting language
- **Azure DevOps CLI**: Data retrieval
- **Chart.js**: Interactive visualizations
- **HTML5/CSS3**: Report presentation
- **JSON**: Data serialization

### Performance
- **Fetch Time**: ~5-10 minutes for 18 repositories
- **Processing Time**: ~2-3 minutes for 730 PRs
- **Total Runtime**: ~10-15 minutes
- **Report Size**: ~12 KB HTML file

## Contact

For questions or issues with the report:
- Generated by: Triagent PR Report Generator
- Script version: 1.0
- Date: December 24, 2025
