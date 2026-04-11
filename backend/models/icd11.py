"""
ICD-11 Classification Support.
Seeds common ICD-11 codes and provides search/mapping.
ICD-11 is the current WHO standard (ICD-10 is outdated).
"""

import logging
from search.database import get_pool

logger = logging.getLogger(__name__)

# Core ICD-11 codes — a representative seed set
# Full ICD-11 can be loaded from WHO API: https://icd.who.int/icdapi
ICD11_SEED = [
    ("BA00", "Essential hypertension", "Diseases of the circulatory system", "Elevated blood pressure, primary hypertension"),
    ("BA80", "Heart failure", "Diseases of the circulatory system", "Cardiac failure, congestive heart failure, CHF"),
    ("BA41", "Acute myocardial infarction", "Diseases of the circulatory system", "Heart attack, MI, STEMI, NSTEMI"),
    ("BA60", "Atrial fibrillation", "Diseases of the circulatory system", "AFib, AF, irregular heartbeat"),
    ("5A11", "Type 2 diabetes mellitus", "Endocrine diseases", "T2DM, adult-onset diabetes, insulin resistance"),
    ("5A10", "Type 1 diabetes mellitus", "Endocrine diseases", "T1DM, juvenile diabetes, insulin-dependent"),
    ("CA40", "Pneumonia", "Diseases of the respiratory system", "Lung infection, community-acquired pneumonia, CAP"),
    ("CA20", "Asthma", "Diseases of the respiratory system", "Reactive airway disease, bronchial asthma"),
    ("CA22", "COPD", "Diseases of the respiratory system", "Chronic obstructive pulmonary disease, emphysema, chronic bronchitis"),
    ("8B20", "Stroke", "Diseases of the nervous system", "Cerebrovascular accident, CVA, ischemic stroke, brain attack"),
    ("8A00", "Epilepsy", "Diseases of the nervous system", "Seizure disorder, convulsions"),
    ("6A70", "Depressive disorders", "Mental disorders", "Depression, major depressive disorder, MDD"),
    ("6A80", "Anxiety disorders", "Mental disorders", "Generalized anxiety, GAD, panic disorder"),
    ("DA90", "Gastroesophageal reflux disease", "Diseases of the digestive system", "GERD, acid reflux, heartburn"),
    ("DA25", "Crohn disease", "Diseases of the digestive system", "Regional enteritis, Crohn's, inflammatory bowel disease"),
    ("DA26", "Ulcerative colitis", "Diseases of the digestive system", "UC, inflammatory bowel disease"),
    ("GB61", "Chronic kidney disease", "Diseases of the genitourinary system", "CKD, renal failure, kidney failure"),
    ("FA20", "Rheumatoid arthritis", "Diseases of the musculoskeletal system", "RA, autoimmune arthritis"),
    ("FA00", "Osteoarthritis", "Diseases of the musculoskeletal system", "OA, degenerative joint disease, DJD"),
    ("1F20", "COVID-19", "Infectious diseases", "SARS-CoV-2, coronavirus disease"),
    ("1A00", "Cholera", "Infectious diseases", "Vibrio cholerae infection"),
    ("1B90", "Malaria", "Infectious diseases", "Plasmodium infection"),
    ("1C62", "HIV disease", "Infectious diseases", "HIV/AIDS, human immunodeficiency virus"),
    ("1A20", "Typhoid fever", "Infectious diseases", "Salmonella typhi infection, enteric fever"),
    ("1C10", "Tuberculosis", "Infectious diseases", "TB, mycobacterium tuberculosis"),
    ("2B90", "Breast cancer", "Neoplasms", "Breast carcinoma, mammary cancer"),
    ("2C10", "Colorectal cancer", "Neoplasms", "Colon cancer, rectal cancer, CRC"),
    ("2C25", "Lung cancer", "Neoplasms", "Bronchogenic carcinoma, lung carcinoma"),
    ("KA21", "Iron deficiency anaemia", "Diseases of the blood", "IDA, microcytic anemia"),
    ("JA00", "Preeclampsia", "Pregnancy complications", "Toxemia of pregnancy, gestational hypertension with proteinuria"),
    ("EG40", "Eczema", "Diseases of the skin", "Atopic dermatitis, AD"),
    ("EG10", "Psoriasis", "Diseases of the skin", "Plaque psoriasis"),
    ("5B80", "Hypothyroidism", "Endocrine diseases", "Underactive thyroid, Hashimoto's thyroiditis"),
    ("5B70", "Hyperthyroidism", "Endocrine diseases", "Overactive thyroid, Graves' disease, thyrotoxicosis"),
    ("GB70", "Urinary tract infection", "Diseases of the genitourinary system", "UTI, cystitis, pyelonephritis"),
    ("BD10", "Deep vein thrombosis", "Diseases of the circulatory system", "DVT, venous thromboembolism"),
    ("BB01", "Pulmonary embolism", "Diseases of the circulatory system", "PE, pulmonary thromboembolism"),
    ("8A80", "Migraine", "Diseases of the nervous system", "Migraine headache, hemicranial pain"),
    ("DA24", "Peptic ulcer disease", "Diseases of the digestive system", "PUD, gastric ulcer, duodenal ulcer"),
    ("CA08", "Acute bronchitis", "Diseases of the respiratory system", "Chest cold, bronchial infection"),
    ("BA01", "Secondary hypertension", "Diseases of the circulatory system", "Renovascular hypertension, endocrine hypertension"),
    ("5A40", "Metabolic syndrome", "Endocrine diseases", "Syndrome X, insulin resistance syndrome"),
]


async def seed_icd11_codes():
    """Seed the ICD-11 codes table."""
    from search import upsert_icd_code
    count = 0
    for code, title, chapter, synonyms in ICD11_SEED:
        try:
            await upsert_icd_code(
                code=code,
                title=title,
                chapter=chapter,
                description=f"ICD-11 {code}: {title}",
                synonyms=synonyms,
            )
            count += 1
        except Exception as e:
            logger.warning(f"ICD seed error for {code}: {e}")
    logger.info(f"Seeded {count} ICD-11 codes")
    return count


async def lookup_icd11(query: str) -> list[dict]:
    """Search ICD-11 codes by keyword or code."""
    from search import search_icd
    return await search_icd(query)
