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

COUNTRY_LIST = sorted(ADZUNA_COUNTRIES.keys(), key=lambda x: (
    0 if x in ('US', 'United States') else
    1 if x in ('UK', 'United Kingdom') else
    2 if x in ('Canada', 'India', 'Australia') else 3, x
))


def get_adzuna_country_code(country_name):
    return ADZUNA_COUNTRIES.get(country_name)


def _fetch_adzuna_salary(job_title, country_code):
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
    for r in results:
        s_min = r.get('salary_min')
        s_max = r.get('salary_max')
        if s_min and s_max:
            salaries.append((s_min + s_max) / 2)
        elif s_min:
            salaries.append(s_min)
        elif s_max:
            salaries.append(s_max)

    if not salaries:
        return None

    avg = sum(salaries) / len(salaries)
    low = min(salaries)
    high = max(salaries)
    currency = results[0].get('salary_currency', 'USD')
    total_count = data.get('count', len(results))

    return {
        'range': f'{currency} {low:,.0f} – {high:,.0f}',
        'average': f'{currency} {avg:,.0f}',
        'source': 'Adzuna',
        'confidence': f'Based on {total_count} job posting{"s" if total_count != 1 else ""}',
    }


SYSTEM_SALARY = """You are a labor market analyst. Given a job title, industry, years of experience, and country,
estimate the typical annual salary range for this role. Respond with realistic figures in the local currency.

Return JSON in this format:
{"range": "USD 80,000 – 120,000", "average": "USD 100,000", "currency": "USD", "notes": "Estimate based on typical market rates for this role."}"""


def _fetch_llm_salary(job_title, industry, years_exp, country):
    user_prompt = (
        f"Job Title: {job_title}\n"
        f"Industry: {industry}\n"
        f"Years of Experience: {years_exp}\n"
        f"Country: {country}\n\n"
        f"Estimate the typical annual salary range for this role."
    )
    try:
        result = _call_llm(SYSTEM_SALARY, user_prompt)
        return {
            'range': result.get('range', ''),
            'average': result.get('average', ''),
            'source': 'AI Estimated',
            'confidence': 'Estimate based on market data',
        }
    except Exception as e:
        current_app.logger.error(f'LLM salary fetch failed: {e}')
        return {
            'range': 'N/A',
            'average': 'N/A',
            'source': 'Unavailable',
            'confidence': '',
        }


def fetch_salary(job_title, industry, years_exp, country):
    country_code = get_adzuna_country_code(country) if country else None

    if country_code:
        result = _fetch_adzuna_salary(job_title, country_code)
        if result:
            return result

    return _fetch_llm_salary(job_title, industry, years_exp, country)
