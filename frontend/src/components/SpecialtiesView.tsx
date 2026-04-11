import { useState, useEffect } from 'react';
import type { Specialty } from '../utils/types';
import { fetchSpecialties } from '../utils/api';

// Fallback local data if API unavailable
const FALLBACK_SPECIALTIES: Specialty[] = [
  { id: 'internal_medicine', name: 'Internal Medicine', category: 'clinical' },
  { id: 'family_medicine', name: 'Family Medicine', category: 'clinical' },
  { id: 'emergency_medicine', name: 'Emergency Medicine', category: 'clinical' },
  { id: 'pediatrics', name: 'Pediatrics', category: 'clinical' },
  { id: 'obstetrics_gynecology', name: 'OB/GYN', category: 'clinical' },
  { id: 'general_surgery', name: 'General Surgery', category: 'clinical' },
  { id: 'cardiology', name: 'Cardiology', category: 'clinical' },
  { id: 'neurology', name: 'Neurology', category: 'clinical' },
  { id: 'psychiatry', name: 'Psychiatry', category: 'clinical' },
  { id: 'pulmonology', name: 'Pulmonology', category: 'clinical' },
  { id: 'gastroenterology', name: 'Gastroenterology', category: 'clinical' },
  { id: 'nephrology', name: 'Nephrology', category: 'clinical' },
  { id: 'endocrinology', name: 'Endocrinology', category: 'clinical' },
  { id: 'rheumatology', name: 'Rheumatology', category: 'clinical' },
  { id: 'infectious_disease', name: 'Infectious Disease', category: 'clinical' },
  { id: 'hematology', name: 'Hematology', category: 'clinical' },
  { id: 'oncology', name: 'Oncology', category: 'clinical' },
  { id: 'dermatology', name: 'Dermatology', category: 'clinical' },
  { id: 'orthopedics', name: 'Orthopedics', category: 'clinical' },
  { id: 'ophthalmology', name: 'Ophthalmology', category: 'clinical' },
  { id: 'otolaryngology', name: 'ENT', category: 'clinical' },
  { id: 'urology', name: 'Urology', category: 'clinical' },
  { id: 'geriatrics', name: 'Geriatrics', category: 'clinical' },
  { id: 'radiology', name: 'Radiology', category: 'clinical' },
  { id: 'anesthesiology', name: 'Anesthesiology', category: 'clinical' },
  { id: 'critical_care', name: 'Critical Care', category: 'clinical' },
  { id: 'palliative_medicine', name: 'Palliative Medicine', category: 'clinical' },
  { id: 'preventive_medicine', name: 'Preventive Medicine', category: 'clinical' },
  { id: 'public_health', name: 'Public Health', category: 'clinical' },
  { id: 'anatomy', name: 'Anatomy', category: 'basic_science' },
  { id: 'physiology', name: 'Physiology', category: 'basic_science' },
  { id: 'biochemistry', name: 'Biochemistry', category: 'basic_science' },
  { id: 'pharmacology', name: 'Pharmacology', category: 'basic_science' },
  { id: 'microbiology', name: 'Microbiology', category: 'basic_science' },
  { id: 'immunology', name: 'Immunology', category: 'basic_science' },
  { id: 'genetics', name: 'Genetics', category: 'basic_science' },
  { id: 'epidemiology', name: 'Epidemiology', category: 'basic_science' },
  { id: 'biostatistics', name: 'Biostatistics', category: 'basic_science' },
  { id: 'neuroscience', name: 'Neuroscience', category: 'basic_science' },
  { id: 'pathology', name: 'Pathology', category: 'basic_science' },
];

interface Props {
  onSelect: (specialtyId: string) => void;
}

export default function SpecialtiesView({ onSelect }: Props) {
  const [specialties, setSpecialties] = useState<Specialty[]>(FALLBACK_SPECIALTIES);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchSpecialties().then(setSpecialties).catch(() => {});
  }, []);

  const filtered = searchQuery
    ? specialties.filter(s => s.name.toLowerCase().includes(searchQuery.toLowerCase()))
    : specialties;

  const clinical = filtered.filter(s => s.category === 'clinical');
  const subspecialty = filtered.filter(s => s.category === 'subspecialty');
  const basicScience = filtered.filter(s => s.category === 'basic_science');

  return (
    <div className="list-view">
      <h2 className="list-title" style={{ marginBottom: 16 }}>Specialties</h2>
      <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', marginBottom: 16 }}>
        Select a specialty to filter search results.
      </p>

      <input
        type="text"
        className="list-search"
        placeholder="Search specialties…"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      <button
        className="specialty-chip"
        style={{ width: '100%', marginBottom: 16, background: 'var(--accent-light)', color: 'var(--accent-text)', borderColor: 'var(--accent)' }}
        onClick={() => onSelect('')}
      >
        All Specialties
      </button>

      {clinical.length > 0 && (
        <>
          <div className="specialty-category">Clinical Specialties</div>
          <div className="specialty-grid">
            {clinical.map(s => (
              <button key={s.id} className="specialty-chip" onClick={() => onSelect(s.id)}>
                {s.name}
              </button>
            ))}
          </div>
        </>
      )}

      {subspecialty.length > 0 && (
        <>
          <div className="specialty-category">Subspecialties</div>
          <div className="specialty-grid">
            {subspecialty.map(s => (
              <button key={s.id} className="specialty-chip" onClick={() => onSelect(s.id)}>
                {s.name}
              </button>
            ))}
          </div>
        </>
      )}

      {basicScience.length > 0 && (
        <>
          <div className="specialty-category">Basic Sciences</div>
          <div className="specialty-grid">
            {basicScience.map(s => (
              <button key={s.id} className="specialty-chip" onClick={() => onSelect(s.id)}>
                {s.name}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
