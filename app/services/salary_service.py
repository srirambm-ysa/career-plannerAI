import json
import urllib.request
import urllib.parse
import urllib.error
from flask import current_app
from app.services.ai_service import _call_llm

ADZUNA_COUNTRIES = {
    'US': 'us', 'United States': 'us', 'USA': 'us',
    'UK': 'gb', 'United Kingdom': 'gb', 'GB': 'gb',
    'Canada': 'ca', 'CA': 'ca',
    'Australia': 'au', 'AU': 'au',
    'India': 'in', 'IN': 'in',
    'New Zealand': 'nz', 'NZ': 'nz',
    'Singapore': 'sg', 'SG': 'sg',
    'South Africa': 'za', 'ZA': 'za',
    'Ireland': 'ie', 'IE': 'ie',
    'Netherlands': 'nl', 'NL': 'nl',
    'Germany': 'de', 'DE': 'de',
    'France': 'fr', 'FR': 'fr',
    'Austria': 'at', 'AT': 'at',
    'Switzerland': 'ch', 'CH': 'ch',
    'Belgium': 'be', 'BE': 'be',
    'Luxembourg': 'lu', 'LU': 'lu',
    'Poland': 'pl', 'PL': 'pl',
    'Sweden': 'se', 'SE': 'se',
    'Denmark': 'dk', 'DK': 'dk',
    'Norway': 'no', 'NO': 'no',
    'Finland': 'fi', 'FI': 'fi',
    'Czech Republic': 'cz', 'CZ': 'cz',
    'Romania': 'ro', 'RO': 'ro',
    'Hungary': 'hu', 'HU': 'hu',
}

CURRENCY_MAP = {
    'US': 'USD', 'United States': 'USD', 'USA': 'USD',
    'UK': 'GBP', 'United Kingdom': 'GBP', 'GB': 'GBP',
    'Canada': 'CAD', 'CA': 'CAD',
    'Australia': 'AUD', 'AU': 'AUD',
    'India': 'INR', 'IN': 'INR',
    'New Zealand': 'NZD', 'NZ': 'NZD',
    'Singapore': 'SGD', 'SG': 'SGD',
    'South Africa': 'ZAR', 'ZA': 'ZAR',
    'Ireland': 'EUR', 'IE': 'EUR',
    'Netherlands': 'EUR', 'NL': 'EUR',
    'Germany': 'EUR', 'DE': 'EUR',
    'France': 'EUR', 'FR': 'EUR',
    'Austria': 'EUR', 'AT': 'EUR',
    'Switzerland': 'CHF', 'CH': 'CHF',
    'Belgium': 'EUR', 'BE': 'EUR',
    'Luxembourg': 'EUR', 'LU': 'EUR',
    'Poland': 'PLN', 'PL': 'PLN',
    'Sweden': 'SEK', 'SE': 'SEK',
    'Denmark': 'DKK', 'DK': 'DKK',
    'Norway': 'NOK', 'NO': 'NOK',
    'Finland': 'EUR', 'FI': 'EUR',
    'Czech Republic': 'CZK', 'CZ': 'CZK',
    'Romania': 'RON', 'RO': 'RON',
    'Hungary': 'HUF', 'HU': 'HUF',
}

COUNTRY_LIST = sorted(ADZUNA_COUNTRIES.keys(), key=lambda x: (
    0 if x in ('US', 'United States') else
    1 if x in ('UK', 'United Kingdom') else
    2 if x in ('Canada', 'India', 'Australia') else 3, x
))


def get_adzuna_country_code(country_name):
    return ADZUNA_COUNTRIES.get(country_name)


def _fetch_adzuna_salary(job_title, country_code, country_name=None):
    app_id = current_app.config.get('ADZUNA_APP_ID', '')
    api_key = current_app.config.get('ADZUNA_API_KEY', '')
    if not app_id or not api_key:
        return None

    params = urllib.parse.urlencode({
        'app_id': app_id,
        'app_key': api_key,
        'what': job_title,
        'results_per_page': 20,
        'content-type': 'application/json',
    })
    url = f'https://api.adzuna.com/v1/api/jobs/{country_code}/search/1?{params}'

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CareerPlanner/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        current_app.logger.warning(f'Adzuna API call failed: {e}')
        return None

    results = data.get('results', [])
    if not results:
        return None

    salaries = []
    company_counts = {}
    for r in results:
        s_min = r.get('salary_min')
        s_max = r.get('salary_max')
        if s_min and s_max:
            salaries.append((s_min + s_max) / 2)
        elif s_min:
            salaries.append(s_min)
        elif s_max:
            salaries.append(s_max)

        company = r.get('company', {})
        name = company.get('display_name') if company else None
        if name:
            company_counts[name] = company_counts.get(name, 0) + 1

    if not salaries:
        return None

    avg = sum(salaries) / len(salaries)
    low = min(salaries)
    high = max(salaries)
    api_currency = results[0].get('salary_currency', 'USD')
    currency = CURRENCY_MAP.get(country_name, api_currency)
    total_count = data.get('count', len(results))

    top_hirers = sorted(company_counts.items(), key=lambda x: -x[1])[:5]
    top_hirers_list = [
        {'name': name, 'count': count}
        for name, count in top_hirers
    ]

    return {
        'range': f'{currency} {low:,.0f} – {high:,.0f}',
        'average': f'{currency} {avg:,.0f}',
        'source': 'Adzuna',
        'confidence': f'Based on {len(results)} of {total_count} job posting{"s" if total_count != 1 else ""}',
        'top_hirers': top_hirers_list,
    }


SYSTEM_SALARY = """You are a labor market analyst. Given a job title, industry, years of experience, and country,
estimate the typical annual salary range for this role. Respond with realistic figures in the local currency.

Return JSON in this format:
{"range": "GBP 80,000 – 120,000", "average": "GBP 100,000", "currency": "GBP", "notes": "Estimate based on typical market rates for this role."}"""


def _fetch_llm_salary(job_title, industry, years_exp, country):
    currency = CURRENCY_MAP.get(country, 'USD')
    user_prompt = (
        f"Job Title: {job_title}\n"
        f"Industry: {industry}\n"
        f"Years of Experience: {years_exp}\n"
        f"Country: {country}\n\n"
        f"Estimate the typical annual salary range for this role "
        f"in {currency}. Use {currency} format."
    )
    try:
        result = _call_llm(SYSTEM_SALARY, user_prompt)
        return {
            'range': result.get('range', ''),
            'average': result.get('average', ''),
            'source': 'AI Estimated',
            'confidence': 'Estimate based on market data',
            'top_hirers': [],
        }
    except Exception as e:
        current_app.logger.error(f'LLM salary fetch failed: {e}')
        return {
            'range': 'N/A',
            'average': 'N/A',
            'source': 'Unavailable',
            'confidence': '',
            'top_hirers': [],
        }


def fetch_salary(job_title, industry, years_exp, country):
    country_code = get_adzuna_country_code(country) if country else None

    if country_code:
        result = _fetch_adzuna_salary(job_title, country_code, country)
        if result:
            return result

    return _fetch_llm_salary(job_title, industry, years_exp, country)
