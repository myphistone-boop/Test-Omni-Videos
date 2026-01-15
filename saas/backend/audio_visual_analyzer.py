"""
Audio-Visual Analyzer - Détection de temps forts
Sans transcription, rapide et gratuit
"""

import os
import subprocess
import numpy as np
import cv2
from datetime import datetime
from typing import List, Dict, Tuple


def log(message: str, level: str = "INFO"):
    """Logging avec timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    prefix = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "•")
    print(f"[{timestamp}] {prefix} {message}")


def extract_audio_features(video_path: str) -> Dict:
    """
    Extrait les features audio SANS transcription
    Utilise ffmpeg + numpy uniquement (pas besoin de librosa)

    Returns:
        {
            'energy': np.array,  # Énergie RMS par fenêtre de 0.5s
            'timestamps': np.array,  # Timestamps correspondants
            'silence_periods': [(start, end), ...],  # Périodes de silence
            'peaks': [timestamp, ...]  # Pics d'énergie
        }
    """
    log("=" * 80)
    log("🎵 ANALYSE AUDIO", "INFO")
    log("=" * 80)

    log(f"Vidéo : {video_path}", "DEBUG")

    # Extraire l'audio en PCM 16kHz mono
    audio_file = "/tmp/temp_audio.wav"
    log("Extraction audio avec ffmpeg...", "INFO")

    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-ac', '1',  # Mono
        '-ar', '16000',  # 16kHz
        '-f', 'wav',
        audio_file
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"Erreur ffmpeg : {result.stderr}", "ERROR")
        return None

    log(f"✅ Audio extrait : {audio_file}", "SUCCESS")

    # Lire l'audio avec scipy ou wave
    import wave
    with wave.open(audio_file, 'rb') as wav:
        sample_rate = wav.getframerate()
        n_frames = wav.getnframes()
        audio_data = wav.readframes(n_frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

    log(f"Sample rate : {sample_rate} Hz", "DEBUG")
    log(f"Durée : {len(audio_array) / sample_rate:.1f}s", "DEBUG")
    log(f"Samples : {len(audio_array)}", "DEBUG")

    # Calculer l'énergie RMS par fenêtre de 0.5s
    window_size = int(0.5 * sample_rate)  # 0.5 secondes
    hop_size = int(0.25 * sample_rate)    # Hop de 0.25s (overlap 50%)

    log(f"Fenêtre : {window_size} samples ({window_size/sample_rate:.2f}s)", "DEBUG")
    log(f"Hop : {hop_size} samples ({hop_size/sample_rate:.2f}s)", "DEBUG")

    energies = []
    timestamps = []

    for i in range(0, len(audio_array) - window_size, hop_size):
        window = audio_array[i:i + window_size]
        rms = np.sqrt(np.mean(window ** 2))
        energies.append(rms)
        timestamps.append(i / sample_rate)

    energies = np.array(energies)
    timestamps = np.array(timestamps)

    log(f"✅ {len(energies)} fenêtres d'énergie calculées", "SUCCESS")
    log(f"Énergie min : {energies.min():.4f}", "DEBUG")
    log(f"Énergie max : {energies.max():.4f}", "DEBUG")
    log(f"Énergie moyenne : {energies.mean():.4f}", "DEBUG")

    # Détecter les silences (énergie < seuil)
    silence_threshold = np.percentile(energies, 20)  # 20ème percentile
    log(f"Seuil de silence : {silence_threshold:.4f}", "DEBUG")

    silence_periods = []
    in_silence = False
    silence_start = None

    for i, (ts, energy) in enumerate(zip(timestamps, energies)):
        if energy < silence_threshold and not in_silence:
            silence_start = ts
            in_silence = True
        elif energy >= silence_threshold and in_silence:
            if silence_start is not None and (ts - silence_start) >= 0.4:  # Au moins 0.4s
                silence_periods.append((silence_start, ts))
            in_silence = False
            silence_start = None

    log(f"✅ {len(silence_periods)} périodes de silence détectées", "SUCCESS")
    for start, end in silence_periods[:5]:
        log(f"   • {start:.1f}s - {end:.1f}s (durée: {end-start:.1f}s)", "DEBUG")

    # Détecter les pics d'énergie
    energy_threshold = np.percentile(energies, 75)  # 75ème percentile
    log(f"Seuil de pic : {energy_threshold:.4f}", "DEBUG")

    peaks = []
    for i, (ts, energy) in enumerate(zip(timestamps, energies)):
        if energy > energy_threshold:
            # Vérifier que c'est un maximum local
            is_peak = True
            for j in range(max(0, i-2), min(len(energies), i+3)):
                if j != i and energies[j] > energy:
                    is_peak = False
                    break
            if is_peak:
                peaks.append(ts)

    log(f"✅ {len(peaks)} pics d'énergie détectés", "SUCCESS")
    for ts in peaks[:10]:
        log(f"   • {ts:.1f}s", "DEBUG")

    # Nettoyer
    try:
        os.remove(audio_file)
    except:
        pass

    log("")

    return {
        'energy': energies,
        'timestamps': timestamps,
        'silence_periods': silence_periods,
        'peaks': peaks
    }


def extract_visual_features(video_path: str, segments: List[Tuple[float, float]], fps: int = 2) -> Dict:
    """
    Analyse visuelle UNIQUEMENT sur les segments candidats
    Utilise différence d'images (ultra rapide)

    Args:
        video_path: Chemin vidéo
        segments: Liste de (start, end) en secondes
        fps: Frames par seconde à analyser (défaut: 2 fps = 1 frame toutes les 0.5s)

    Returns:
        {
            'motion_scores': {segment_idx: score},
            'frame_count': int
        }
    """
    log("=" * 80)
    log("🎬 ANALYSE VISUELLE", "INFO")
    log("=" * 80)

    log(f"Vidéo : {video_path}", "DEBUG")
    log(f"Nombre de segments à analyser : {len(segments)}", "INFO")
    log(f"FPS d'analyse : {fps}", "DEBUG")

    motion_scores = {}
    total_frames = 0

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        log("Impossible d'ouvrir la vidéo", "ERROR")
        return {'motion_scores': {}, 'frame_count': 0}

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    log(f"FPS vidéo : {video_fps}", "DEBUG")

    for seg_idx, (start, end) in enumerate(segments):
        log(f"Segment #{seg_idx} : {start:.1f}s - {end:.1f}s", "INFO")

        # Se positionner au début du segment
        cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)

        prev_frame = None
        motion_values = []
        frames_analyzed = 0

        current_time = start
        frame_interval = 1.0 / fps  # Intervalle entre frames

        while current_time < end:
            # Lire la frame
            ret, frame = cap.read()
            if not ret:
                break

            # Convertir en grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 180))  # Réduire pour vitesse

            if prev_frame is not None:
                # Calculer différence
                diff = cv2.absdiff(gray, prev_frame)
                motion = np.mean(diff)
                motion_values.append(motion)

            prev_frame = gray.copy()
            frames_analyzed += 1
            total_frames += 1

            # Avancer au prochain timestamp
            current_time += frame_interval
            cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)

        # Score du segment = moyenne du mouvement
        if motion_values:
            avg_motion = np.mean(motion_values)
            motion_scores[seg_idx] = avg_motion
            log(f"   → {frames_analyzed} frames analysées, mouvement moyen : {avg_motion:.2f}", "SUCCESS")
        else:
            motion_scores[seg_idx] = 0.0
            log(f"   → Aucune frame analysée", "WARNING")

    cap.release()

    log(f"✅ Analyse visuelle terminée : {total_frames} frames totales", "SUCCESS")
    log("")

    return {
        'motion_scores': motion_scores,
        'frame_count': total_frames
    }


def detect_candidate_segments(audio_features: Dict, video_duration: float, max_candidates: int = 15) -> List[Dict]:
    """
    Détecte les segments candidats basés sur l'audio

    Heuristiques :
    - Silence suivi d'un pic d'énergie (pattern silence → punch)
    - Énergie soutenue sur plusieurs secondes
    - Variation d'énergie (changement de rythme)

    Returns:
        [
            {
                'start': float,
                'end': float,
                'audio_score': float,
                'reason': str
            }
        ]
    """
    log("=" * 80)
    log("🎯 DÉTECTION SEGMENTS CANDIDATS", "INFO")
    log("=" * 80)

    candidates = []

    energies = audio_features['energy']
    timestamps = audio_features['timestamps']
    silence_periods = audio_features['silence_periods']
    peaks = audio_features['peaks']

    log(f"Silences disponibles : {len(silence_periods)}", "DEBUG")
    log(f"Pics disponibles : {len(peaks)}", "DEBUG")

    # Stratégie 1: Silence → Pic (très fort indicateur)
    log("Stratégie 1 : Silence → Pic d'énergie", "INFO")
    for silence_start, silence_end in silence_periods:
        # Chercher un pic dans les 3 secondes après le silence
        for peak in peaks:
            if silence_end <= peak <= silence_end + 3.0:
                # Segment : 5s avant le pic jusqu'à 35s après
                start = max(0, peak - 5)
                end = min(video_duration, peak + 35)

                # Score basé sur l'énergie au pic
                peak_idx = np.argmin(np.abs(timestamps - peak))
                if peak_idx < len(energies):
                    audio_score = energies[peak_idx]
                    # Normaliser
                    audio_score = min(1.0, audio_score / energies.max())

                    candidates.append({
                        'start': start,
                        'end': end,
                        'audio_score': audio_score,
                        'reason': f'Silence→Pic @{peak:.1f}s'
                    })
                    log(f"   ✅ Candidat : {start:.1f}s - {end:.1f}s (score: {audio_score:.2f}) - {candidates[-1]['reason']}", "SUCCESS")
                    break

    # Stratégie 2: Énergie soutenue (> 10s au-dessus du 70ème percentile)
    log("Stratégie 2 : Énergie soutenue", "INFO")
    energy_threshold = np.percentile(energies, 70)

    high_energy_start = None
    for i, (ts, energy) in enumerate(zip(timestamps, energies)):
        if energy > energy_threshold:
            if high_energy_start is None:
                high_energy_start = ts
        else:
            if high_energy_start is not None:
                duration = ts - high_energy_start
                if duration >= 10.0:  # Au moins 10s d'énergie soutenue
                    start = max(0, high_energy_start - 2)
                    end = min(video_duration, ts + 2)

                    # Score = durée normalisée
                    audio_score = min(1.0, duration / 30.0)

                    candidates.append({
                        'start': start,
                        'end': end,
                        'audio_score': audio_score,
                        'reason': f'Énergie soutenue {duration:.1f}s @{high_energy_start:.1f}s'
                    })
                    log(f"   ✅ Candidat : {start:.1f}s - {end:.1f}s (score: {audio_score:.2f}) - {candidates[-1]['reason']}", "SUCCESS")

                high_energy_start = None

    # Stratégie 3: Plus grands pics même sans silence avant
    log("Stratégie 3 : Plus grands pics", "INFO")
    top_peaks = sorted(peaks, key=lambda p: energies[np.argmin(np.abs(timestamps - p))], reverse=True)[:10]

    for peak in top_peaks:
        # Vérifier qu'on n'a pas déjà ce segment
        exists = False
        for c in candidates:
            if abs(c['start'] - (peak - 5)) < 5:  # Même région
                exists = True
                break

        if not exists:
            start = max(0, peak - 5)
            end = min(video_duration, peak + 35)

            peak_idx = np.argmin(np.abs(timestamps - peak))
            audio_score = min(1.0, energies[peak_idx] / energies.max())

            candidates.append({
                'start': start,
                'end': end,
                'audio_score': audio_score,
                'reason': f'Top pic @{peak:.1f}s'
            })
            log(f"   ✅ Candidat : {start:.1f}s - {end:.1f}s (score: {audio_score:.2f}) - {candidates[-1]['reason']}", "SUCCESS")

    # Trier par score et garder les meilleurs
    candidates.sort(key=lambda x: x['audio_score'], reverse=True)
    candidates = candidates[:max_candidates]

    log(f"✅ {len(candidates)} candidats au total (max: {max_candidates})", "SUCCESS")
    log("")

    return candidates


def analyze_video(video_path: str, video_duration: float) -> List[Dict]:
    """
    Pipeline complet d'analyse AUDIO UNIQUEMENT (visuel désactivé pour vitesse)

    Returns:
        [
            {
                'start': float,
                'end': float,
                'audio_score': float,
                'visual_score': float,  # Toujours 0 maintenant
                'combined_score': float,
                'reason': str
            }
        ]
        Trié par combined_score décroissant
    """
    log("\n" + "=" * 80)
    log("🚀 DÉMARRAGE ANALYSE AUDIO UNIQUEMENT (visuel désactivé)", "INFO")
    log("=" * 80)
    log(f"Vidéo : {video_path}", "INFO")
    log(f"Durée : {video_duration:.1f}s", "INFO")
    log("")

    # 1. Analyse audio
    audio_features = extract_audio_features(video_path)
    if not audio_features:
        log("Échec analyse audio", "ERROR")
        return []

    # 2. Détecter candidats
    candidates = detect_candidate_segments(audio_features, video_duration, max_candidates=15)
    if not candidates:
        log("Aucun candidat détecté", "WARNING")
        return []

    # 3. SKIP analyse visuelle (trop lent)
    log("=" * 80)
    log("⚡ ANALYSE VISUELLE DÉSACTIVÉE (pour vitesse)", "INFO")
    log("=" * 80)
    log("Utilisation du score audio uniquement")
    log("")

    # 4. Utiliser seulement le score audio
    log("=" * 80)
    log("🎯 CALCUL SCORES (AUDIO UNIQUEMENT)", "INFO")
    log("=" * 80)

    for i, candidate in enumerate(candidates):
        audio_score = candidate['audio_score']
        visual_score = 0.0  # Désactivé

        # Score combiné = 100% audio (pas de visuel)
        combined = audio_score

        candidate['visual_score'] = visual_score
        candidate['combined_score'] = combined

        log(f"Candidat #{i+1} : {candidate['start']:.1f}s - {candidate['end']:.1f}s", "INFO")
        log(f"   Audio : {audio_score:.2f} | Combiné : {combined:.2f}", "DEBUG")
        log(f"   Raison : {candidate['reason']}", "DEBUG")

    # Trier par score combiné
    candidates.sort(key=lambda x: x['combined_score'], reverse=True)

    log("")
    log("=" * 80)
    log(f"✅ TOP 5 CANDIDATS (AUDIO UNIQUEMENT)", "SUCCESS")
    log("=" * 80)
    for i, c in enumerate(candidates[:5]):
        log(f"#{i+1} : {c['start']:.1f}s - {c['end']:.1f}s | Score: {c['combined_score']:.2f} | {c['reason']}", "INFO")
    log("")

    return candidates
