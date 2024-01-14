from enum import Enum


class LinkedInLeadFilter(str, Enum):
    BING_GEO = "REGION"
    TITLE = "TITLE"
    INDUSTRY = "INDUSTRY"
    SCHOOL = "SCHOOL"
    COMPANY = "COMPANY"
    COMPANY_SIZE = "HEADCOUNT"
    COMPANY_TYPE = "COMPANY TYPE"
    SENIORITY = "SENIORITY"
    TENURE = "TENURE"
    FUNCTION = "FUNCTION"

    def __str__(self):
        return self.name


def get_lix_query_parameter_from_linkedin_filter(filter_type: LinkedInLeadFilter) -> str:
    match filter_type.value:
        case 'REGION':
            return 'BING_GEO'
        case 'COMPANY':
            return 'COMPANY_WITH_LIST'
        case 'TITLE':
            return 'TITLE'
        case 'SENIORITY':
            return 'SENIORITY_V2'
        case 'HEADCOUNT':
            return 'COMPANY_SIZE'
        case 'TENURE':
            return 'TENURE'
        case 'INDUSTRY':
            return 'INDUSTRY'
        case 'FUNCTION':
            return 'FUNCTION'
        case 'SCHOOL':
            return 'SCHOOL'
    raise ValueError(f'Could not get relevant LinkedIn filter from {filter_type}')
