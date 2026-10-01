# this file  functionate to prived data for the test. if no key detected, test will use data dummy from faker
# and will use open ai if key detected
import os
import json
from pydantic import BaseModel, Field, ValidationError
from faker import Faker
from openai import OpenAI


class IndoBusinessData(BaseModel):
    company_name: str = Field(..., description="Legal Indonesian company name")
    company_email: str
    company_phone: str
    company_address: str
    industry: str
    customer_name: str
    customer_contact: str
    customer_address: str
    customer_email: str
    contact_person: str


def generate_fallback_data() -> dict:
    fake = Faker("id_ID")
    return {
        "company_name": fake.company(),
        "company_email": fake.company_email(),
        "company_phone": fake.phone_number(),
        "company_address": fake.address().replace("\n", ", "),
        "industry": "Retail",
        "customer_name": fake.company(),  # (Sebaiknya fake.company() untuk nama toko/outlet)
        "customer_contact": fake.phone_number(),
        "customer_address": fake.address().replace("\n", ", "),
        "customer_email": fake.email(),  # <-- TAMBAHKAN INI
        "contact_person": fake.name(),  # <-- TAMBAHKAN INI
    }


def get_test_data(retries=2) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Falling back to Faker.")
        return generate_fallback_data()

    client = OpenAI(
        api_key=api_key, base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    )

    prompt = "Generate coherent, realistic Indonesian business data in strict JSON format. Fields needed: company_name, company_email, company_phone, company_address, industry, customer_name, customer_contact, customer_address, customer_email, contact_person."

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=os.getenv("AI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            raw_data = json.loads(response.choices[0].message.content)
            validated_data = IndoBusinessData(**raw_data)
            return validated_data.model_dump()
        except (ValidationError, json.JSONDecodeError, Exception) as e:
            print(f"AI Generation failed on attempt {attempt+1}: {e}")
            if attempt == retries - 1:
                print("Max retries reached. Falling back to Faker.")
                return generate_fallback_data()
