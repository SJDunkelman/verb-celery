import urllib.parse
import urllib.parse
import time
import requests
import config
from ai import gpt4_ai
from plugins.external_service_automation.linkedin_lead_list.linkedin_filters import LinkedInLeadFilter, get_lix_query_parameter_from_linkedin_filter
from db import supabase_client


def get_linkedin_search_object(api_key: str,
                               query: str,
                               search_type: LinkedInLeadFilter | str,
                               count: int = 100,
                               start: int = 0) -> dict:
    base_url = "https://api.lix-it.com/v1/search/sales/facet"
    query_params = {
        'query': query,
        'count': count,
        'start': start
    }
    if isinstance(search_type, LinkedInLeadFilter):
        query_params['type'] = str(search_type)
    elif isinstance(search_type, str):
        query_params['type'] = search_type
    else:
        raise TypeError(f"Invalid search_type: {search_type}")
    headers = {
        'Authorization': api_key
    }
    url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
    time.sleep(3)
    response = requests.request("GET", url, headers=headers, data={})
    return response.json()


def get_linkedin_sales_navigator_leads(linkedin_search_url: str, number_leads: int) -> list[dict]:
    base_lix_url = "https://api.lix-it.com/v1/li/sales/search/people?url=" + linkedin_search_url
    payload = {}
    headers = {
        'Authorization': config.LIX_API_KEY
    }

    all_results = []
    sequence_id = None
    while number_leads > 0:
        lix_url = base_lix_url
        if sequence_id:
            lix_url += f"&sequence_id={sequence_id}"

        time.sleep(3)
        response = requests.get(lix_url, headers=headers, data=payload)
        data = response.json()

        leads_data = data.get('people', {})
        all_results.extend(leads_data)
        number_leads -= len(leads_data)

        # Check if more leads are available
        total_available = data.get('paging', {}).get('total', 0)
        if total_available <= len(all_results):
            break

        # Update the sequence_id for the next request
        sequence_id = data.get('meta', {}).get('sequenceId')
    return all_results


def create_linkedin_search_url(filter_values: dict[LinkedInLeadFilter, str | list[str]]):
    # Get LinkedIn ID for each search facet
    search_url_queries = []
    for linkedin_filter, values in filter_values.items():
        query_embedding = gpt4_ai.get_embedding('Sales leader')
        match_linkedin_search_facet = supabase_client.rpc('match_linkedin_search_facet_with_type',
                                                          {'query_embedding': query_embedding,
                                                           'match_threshold': 0.8,
                                                           'match_count': 10,
                                                           'search_filter_type': linkedin_filter,
                                                           }).execute()
        if match_linkedin_search_facet.data:
            url_filter_type = linkedin_filter.value.upper()
            filter_id = match_linkedin_search_facet.data[0]['linkedin_id']
            filter_part = f"(type%3A{url_filter_type}%2Cvalues%3AList((id%3A{filter_id}%2Ctext%3A{urllib.parse.quote(url_filter_type)}%2CselectionType%3AINCLUDED)))"
            search_url_queries.append(filter_part)

    base_url = "https://www.linkedin.com/sales/search/people?query="
    filters_str = "%2C".join(search_url_queries)
    query = f"(recentSearchParam%3A(doLogHistory%3Atrue)%2Cfilters%3AList({filters_str}))"
    linkedin_url = f"{base_url}{query}"
    # linkedin_url = urllib.parse.quote(linkedin_url, safe='')
    return linkedin_url


def get_linkedin_search_facets(filter_values: dict[LinkedInLeadFilter, str | list[str]]
                               ) -> dict[LinkedInLeadFilter, list[dict]]:
    search_facets = {}
    for linkedin_filter, values in filter_values.items():
        if values is None:
            continue

        # Ensure values are in a list even if a single value is provided
        if not isinstance(values, list):
            values = [values]

        for value in values:
            facets_for_filter = get_linkedin_search_object(api_key=config.LIX_API_KEY,
                                                           query=value,
                                                           search_type=get_lix_query_parameter_from_linkedin_filter(
                                                               linkedin_filter))

            if 'elements' in facets_for_filter['data']:
                if linkedin_filter in search_facets.keys():
                    search_facets[linkedin_filter].append(facets_for_filter['data']['elements'])
                else:
                    search_facets[linkedin_filter] = facets_for_filter['data']['elements']
                # Save search facets to database
                if linkedin_filter == LinkedInLeadFilter.COMPANY:
                    for company in facets_for_filter['data']['elements'][0]['children']:
                        supabase_client.table('vendor_linkedin_search_facet').insert(
                            {
                                'linkedin_id': str(company['id']),
                                'display_value': company['headline'],
                                'search_filter_type': linkedin_filter,
                            }).execute()
                else:
                    supabase_client.table('vendor_linkedin_search_facet').insert((
                        [{
                            'linkedin_id': str(f['id']),
                            'display_value': f['displayValue'],
                            'search_filter_type': linkedin_filter,
                        } for f in facets_for_filter['data']['elements']]
                    )).execute()
            else:
                search_facets[linkedin_filter] = []
    return search_facets

