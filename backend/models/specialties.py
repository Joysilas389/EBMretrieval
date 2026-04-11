"""
Medical specialty taxonomy — used for routing, filtering, tagging, and browsing.
"""

from dataclasses import dataclass


@dataclass
class Specialty:
    id: str
    name: str
    category: str
    parent: str | None = None
    keywords: list[str] | None = None


SPECIALTIES: list[Specialty] = [
    # CLINICAL
    Specialty("internal_medicine", "Internal Medicine", "clinical", keywords=["internist", "general medicine"]),
    Specialty("family_medicine", "Family Medicine", "clinical", keywords=["family doctor", "primary care", "GP"]),
    Specialty("emergency_medicine", "Emergency Medicine", "clinical", keywords=["ER", "A&E", "emergency"]),
    Specialty("pediatrics", "Pediatrics", "clinical", keywords=["children", "child", "neonatal"]),
    Specialty("obstetrics_gynecology", "Obstetrics & Gynecology", "clinical", keywords=["OB/GYN", "pregnancy", "women's health"]),
    Specialty("general_surgery", "General Surgery", "clinical", keywords=["surgical", "operation"]),
    Specialty("anesthesiology", "Anesthesiology", "clinical", keywords=["anesthesia", "sedation"]),
    Specialty("critical_care", "Critical Care Medicine", "clinical", keywords=["ICU", "intensive care"]),
    Specialty("psychiatry", "Psychiatry", "clinical", keywords=["mental health", "psychiatric"]),
    Specialty("neurology", "Neurology", "clinical", keywords=["brain", "nerve", "neurological"]),
    Specialty("neurosurgery", "Neurosurgery", "clinical", keywords=["brain surgery"]),
    Specialty("cardiology", "Cardiology", "clinical", keywords=["heart", "cardiac"]),
    Specialty("cardiothoracic_surgery", "Cardiothoracic Surgery", "clinical"),
    Specialty("pulmonology", "Pulmonology", "clinical", keywords=["lung", "respiratory", "pulmonary"]),
    Specialty("gastroenterology", "Gastroenterology", "clinical", keywords=["GI", "digestive", "stomach", "liver"]),
    Specialty("hepatology", "Hepatology", "clinical", keywords=["liver"]),
    Specialty("nephrology", "Nephrology", "clinical", keywords=["kidney", "renal"]),
    Specialty("endocrinology", "Endocrinology", "clinical", keywords=["hormone", "diabetes", "thyroid"]),
    Specialty("rheumatology", "Rheumatology", "clinical", keywords=["autoimmune", "arthritis", "joints"]),
    Specialty("infectious_disease", "Infectious Disease", "clinical", keywords=["infection", "antibiotic", "virus"]),
    Specialty("hematology", "Hematology", "clinical", keywords=["blood", "anemia", "clotting"]),
    Specialty("oncology", "Medical Oncology", "clinical", keywords=["cancer", "tumor", "chemotherapy"]),
    Specialty("radiation_oncology", "Radiation Oncology", "clinical"),
    Specialty("dermatology", "Dermatology", "clinical", keywords=["skin", "rash"]),
    Specialty("allergy_immunology", "Allergy & Immunology", "clinical", keywords=["allergy", "asthma"]),
    Specialty("ophthalmology", "Ophthalmology", "clinical", keywords=["eye", "vision"]),
    Specialty("otolaryngology", "Otolaryngology / ENT", "clinical", keywords=["ear", "nose", "throat", "ENT"]),
    Specialty("orthopedics", "Orthopedic Surgery", "clinical", keywords=["bone", "fracture", "joint"]),
    Specialty("urology", "Urology", "clinical", keywords=["bladder", "prostate"]),
    Specialty("vascular_surgery", "Vascular Surgery", "clinical"),
    Specialty("plastic_surgery", "Plastic Surgery", "clinical"),
    Specialty("geriatrics", "Geriatrics", "clinical", keywords=["elderly", "aging"]),
    Specialty("palliative_medicine", "Palliative Medicine", "clinical", keywords=["hospice", "end of life"]),
    Specialty("pain_medicine", "Pain Medicine", "clinical"),
    Specialty("sports_medicine", "Sports Medicine", "clinical"),
    Specialty("rehabilitation", "PM&R / Rehabilitation", "clinical"),
    Specialty("preventive_medicine", "Preventive Medicine", "clinical", keywords=["screening", "prevention"]),
    Specialty("public_health", "Public Health", "clinical", keywords=["epidemiology", "population health"]),
    Specialty("pathology", "Pathology", "clinical"),
    Specialty("radiology", "Radiology", "clinical", keywords=["X-ray", "CT", "MRI", "imaging"]),
    Specialty("nuclear_medicine", "Nuclear Medicine", "clinical"),
    Specialty("sleep_medicine", "Sleep Medicine", "clinical"),
    Specialty("neonatology", "Neonatology", "clinical", parent="pediatrics"),
    Specialty("dentistry", "Dentistry", "clinical"),
    # SUBSPECIALTIES
    Specialty("pediatric_cardiology", "Pediatric Cardiology", "subspecialty", parent="pediatrics"),
    Specialty("pediatric_neurology", "Pediatric Neurology", "subspecialty", parent="pediatrics"),
    Specialty("maternal_fetal", "Maternal-Fetal Medicine", "subspecialty", parent="obstetrics_gynecology"),
    Specialty("transplant", "Transplant Medicine", "subspecialty"),
    Specialty("interventional_cardiology", "Interventional Cardiology", "subspecialty", parent="cardiology"),
    Specialty("electrophysiology", "Electrophysiology", "subspecialty", parent="cardiology"),
    Specialty("trauma_surgery", "Trauma Surgery", "subspecialty", parent="general_surgery"),
    # BASIC SCIENCES
    Specialty("anatomy", "Anatomy", "basic_science"),
    Specialty("physiology", "Physiology", "basic_science"),
    Specialty("biochemistry", "Biochemistry", "basic_science"),
    Specialty("pharmacology", "Pharmacology", "basic_science", keywords=["drug", "medication"]),
    Specialty("histology", "Histology", "basic_science"),
    Specialty("embryology", "Embryology", "basic_science"),
    Specialty("genetics", "Genetics", "basic_science", keywords=["gene", "DNA"]),
    Specialty("molecular_biology", "Molecular Biology", "basic_science"),
    Specialty("microbiology", "Microbiology", "basic_science", keywords=["bacteria", "virus", "fungus"]),
    Specialty("immunology", "Immunology", "basic_science", keywords=["immune"]),
    Specialty("neuroscience", "Neuroscience", "basic_science"),
    Specialty("epidemiology", "Epidemiology", "basic_science"),
    Specialty("biostatistics", "Biostatistics", "basic_science"),
    Specialty("pharmacokinetics", "Pharmacokinetics", "basic_science"),
    Specialty("pharmacodynamics", "Pharmacodynamics", "basic_science"),
]


def get_specialty(sid: str) -> Specialty | None:
    return next((s for s in SPECIALTIES if s.id == sid), None)


def get_clinical_specialties() -> list[Specialty]:
    return [s for s in SPECIALTIES if s.category == "clinical"]


def get_basic_sciences() -> list[Specialty]:
    return [s for s in SPECIALTIES if s.category == "basic_science"]


def get_all_specialty_ids() -> list[str]:
    return [s.id for s in SPECIALTIES]


def classify_query_specialty(query: str) -> list[str]:
    """Simple keyword-based specialty classification."""
    query_lower = query.lower()
    matched = []
    for spec in SPECIALTIES:
        if spec.keywords:
            for kw in spec.keywords:
                if kw.lower() in query_lower:
                    matched.append(spec.id)
                    break
        if spec.name.lower() in query_lower:
            matched.append(spec.id)
    return list(set(matched)) or ["internal_medicine"]
