import { useState, useEffect } from 'react';
import type { Settings } from '../utils/types';
import { fetchLanguages } from '../utils/api';

interface Props {
  settings: Settings;
  onUpdate: <K extends keyof Settings>(key: K, value: Settings[K]) => void;
  onReset: () => void;
  onClearHistory: () => void;
  onClearBookmarks: () => void;
}

const WORD_LABELS: Record<number, string> = { 200: 'Short', 500: 'Brief', 1000: 'Medium', 2000: 'Standard', 4000: 'Long', 8000: 'Very Long', 16000: 'Max Context' };
function getWordLabel(val: number): string {
  const keys = Object.keys(WORD_LABELS).map(Number).sort((a, b) => a - b);
  let closest = keys[0];
  for (const k of keys) { if (Math.abs(k - val) < Math.abs(closest - val)) closest = k; }
  return WORD_LABELS[closest] || `${val} words`;
}

export default function SettingsView({ settings, onUpdate, onReset, onClearHistory, onClearBookmarks }: Props) {
  const [languages, setLanguages] = useState<Record<string, string>>({ en: 'English' });

  useEffect(() => {
    fetchLanguages().then(setLanguages).catch(() => {});
  }, []);

  return (
    <div className="settings-view">
      <h2 className="list-title" style={{ marginBottom: 24 }}>Settings</h2>

      {/* Appearance */}
      <div className="settings-group">
        <div className="settings-group-title">Appearance</div>
        <div className="setting-row">
          <div className="setting-label">Theme</div>
          <select className="setting-select" value={settings.theme} onChange={(e) => onUpdate('theme', e.target.value as any)}>
            <option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option>
          </select>
        </div>
        <div className="setting-row">
          <div><div className="setting-label">Font Size</div><div className="setting-desc">{settings.fontSize}px</div></div>
          <input type="range" className="setting-slider" min={12} max={22} step={1} value={settings.fontSize} onChange={(e) => onUpdate('fontSize', Number(e.target.value))} />
        </div>
        <div className="setting-row">
          <div className="setting-label">Reduced Motion</div>
          <button className={`setting-toggle ${settings.reducedMotion ? 'active' : ''}`} onClick={() => onUpdate('reducedMotion', !settings.reducedMotion)} />
        </div>
      </div>

      {/* Language */}
      <div className="settings-group">
        <div className="settings-group-title">Language</div>
        <div className="setting-row">
          <div><div className="setting-label">Interface Language</div><div className="setting-desc">Queries auto-translated to English for retrieval, answers translated back</div></div>
          <select className="setting-select" value={settings.language} onChange={(e) => onUpdate('language', e.target.value)}>
            {Object.entries(languages).map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Answer Style */}
      <div className="settings-group">
        <div className="settings-group-title">Answer Style</div>
        <div className="setting-row">
          <div className="setting-label">Style</div>
          <select className="setting-select" value={settings.answerStyle} onChange={(e) => onUpdate('answerStyle', e.target.value as any)}>
            <option value="concise">Concise</option><option value="standard">Standard</option><option value="deep">Deep</option>
          </select>
        </div>
        <div className="setting-row">
          <div className="setting-label">Teaching Mode</div>
          <button className={`setting-toggle ${settings.teachingMode ? 'active' : ''}`} onClick={() => onUpdate('teachingMode', !settings.teachingMode)} />
        </div>
        <div className="setting-row">
          <div className="setting-label">Citation Density</div>
          <select className="setting-select" value={settings.citationDensity} onChange={(e) => onUpdate('citationDensity', e.target.value as any)}>
            <option value="standard">Standard</option><option value="high">High</option><option value="dense">Dense</option>
          </select>
        </div>
        <div className="setting-row">
          <div><div className="setting-label">Answer Length</div><div className="setting-desc">{getWordLabel(settings.maxWords)} (~{settings.maxWords.toLocaleString()} words)</div></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="range" className="setting-slider" min={200} max={16000} step={200} value={settings.maxWords} onChange={(e) => onUpdate('maxWords', Number(e.target.value))} />
            <span className="setting-slider-value">{settings.maxWords.toLocaleString()}</span>
          </div>
        </div>
        <div className="setting-row">
          <div className="setting-label">Max Sources</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="range" className="setting-slider" min={3} max={30} step={1} value={settings.maxSources} onChange={(e) => onUpdate('maxSources', Number(e.target.value))} />
            <span className="setting-slider-value">{settings.maxSources}</span>
          </div>
        </div>
      </div>

      {/* Sources */}
      <div className="settings-group">
        <div className="settings-group-title">Sources</div>
        <div className="setting-row">
          <div className="setting-label">Source Preference</div>
          <select className="setting-select" value={settings.sourcePreference} onChange={(e) => onUpdate('sourcePreference', e.target.value as any)}>
            <option value="balanced">Balanced</option><option value="guidelines">Guidelines First</option><option value="studies">Studies First</option><option value="reviews">Reviews First</option>
          </select>
        </div>
        <div className="setting-row">
          <div className="setting-label">Freshness</div>
          <select className="setting-select" value={settings.freshnessPreference} onChange={(e) => onUpdate('freshnessPreference', e.target.value as any)}>
            <option value="latest">Latest First</option><option value="balanced">Balanced</option><option value="landmark">Landmark Allowed</option>
          </select>
        </div>
        <div className="setting-row">
          <div className="setting-label">Include Basic Sciences</div>
          <button className={`setting-toggle ${settings.includeBasicScience ? 'active' : ''}`} onClick={() => onUpdate('includeBasicScience', !settings.includeBasicScience)} />
        </div>
        <div className="setting-row">
          <div><div className="setting-label">Specialty Filter</div><div className="setting-desc">{settings.specialtyFilter || 'All specialties'}</div></div>
          {settings.specialtyFilter && <button className="btn btn-ghost" onClick={() => onUpdate('specialtyFilter', null)}>Clear</button>}
        </div>
      </div>

      {/* Data */}
      <div className="settings-group">
        <div className="settings-group-title">Data</div>
        <div className="setting-row"><div className="setting-label">Clear History</div><button className="btn btn-ghost" style={{ color: 'var(--danger)' }} onClick={onClearHistory}>Clear</button></div>
        <div className="setting-row"><div className="setting-label">Clear Bookmarks</div><button className="btn btn-ghost" style={{ color: 'var(--danger)' }} onClick={onClearBookmarks}>Clear</button></div>
        <div className="setting-row"><div className="setting-label">Reset All Settings</div><button className="btn btn-ghost" style={{ color: 'var(--danger)' }} onClick={onReset}>Reset</button></div>
      </div>

      {/* About */}
      <div className="settings-group">
        <div className="settings-group-title">About</div>
        <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          <p><strong>EBMRetrieval v3.0</strong> — AI-Powered Evidence Synthesis</p>
          <p style={{ marginTop: 8 }}>AI-powered evidence-based medicine platform. Retrieves from PubMed, WHO, CDC, Europe PMC, MedlinePlus, FDA, NCBI Bookshelf + Claude AI web search for systematic reviews, meta-analyses, and clinical guidelines. ICD-11 classification. 20 interactive physiology simulations. AI-generated simulations for any topic.</p>
          <p style={{ marginTop: 8, color: 'var(--text-tertiary)', fontSize: 'var(--fs-xs)' }}>For educational and clinical reference purposes only. Does not replace professional medical judgment. All settings and history stored locally on your device.</p>
        </div>
      </div>
    </div>
  );
}
