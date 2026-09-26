import os
import cv2
import base64
from PIL import Image
import io

ws_dir = '/home/mehdi/volvo/stairmaster-step-counter'
frames_dir = os.path.join(ws_dir, 'output/white_presentation')

def get_optimized_b64(fname, max_width=1280, quality=82):
    p = os.path.join(frames_dir, fname)
    if not os.path.exists(p):
        return ""
    img = Image.open(p)
    w, h = img.size
    if w > max_width:
        new_h = int(h * (max_width / w))
        img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"

print("Optimizing frames for HTML embedding...")
b64_all = get_optimized_b64('ALL_frame_462.jpg', max_width=1280, quality=80)
b64_s1  = get_optimized_b64('S1_frame_462.jpg', max_width=800, quality=82)
b64_s2  = get_optimized_b64('S2_frame_462.jpg', max_width=800, quality=82)
b64_s3  = get_optimized_b64('S3_frame_462.jpg', max_width=800, quality=82)
b64_s4  = get_optimized_b64('S4_frame_462.jpg', max_width=800, quality=82)
b64_s5  = get_optimized_b64('S5_frame_462.jpg', max_width=800, quality=82)

html_code = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StairMaster Step Counter — Frames & Méthodes / Frames & Methods</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #FFFFFF;
      --surface: #F8FAFC;
      --surface-border: #E2E8F0;
      --text: #0F172A;
      --text-muted: #64748B;
      --primary: #0284C7;
      --primary-light: #E0F2FE;
      --success: #10B981;
      --success-light: #ECFDF5;
      --warning: #F59E0B;
      --danger: #EF4444;
      --purple: #8B5CF6;
      --purple-light: #F5F3FF;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.6;
      padding-bottom: 120px;
      -webkit-font-smoothing: antialiased;
    }}
    .top-nav {{
      position: sticky;
      top: 0;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--surface-border);
      padding: 16px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 100;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 800;
      font-size: 1.15rem;
      letter-spacing: -0.5px;
    }}
    .brand-badge {{
      background: #0F172A;
      color: #FFF;
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 999px;
      font-weight: 700;
    }}
    .nav-links {{
      display: flex;
      gap: 16px;
      align-items: center;
    }}
    .nav-link {{
      color: var(--text-muted);
      text-decoration: none;
      font-weight: 600;
      font-size: 0.9rem;
      transition: color 0.2s;
    }}
    .nav-link:hover {{ color: var(--primary); }}
    .lang-switch {{
      display: flex;
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 999px;
      padding: 4px;
      gap: 4px;
    }}
    .lang-btn {{
      border: none;
      background: transparent;
      padding: 8px 18px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.85rem;
      cursor: pointer;
      color: var(--text-muted);
      transition: all 0.2s ease;
    }}
    .lang-btn.active {{
      background: #FFFFFF;
      color: var(--text);
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 40px 24px 0 24px;
    }}
    .hero {{
      text-align: center;
      padding: 40px 0 50px 0;
      border-bottom: 1px solid var(--surface-border);
    }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 16px;
    }}
    .badge-primary {{ background: var(--primary-light); color: var(--primary); }}
    h1 {{
      font-size: 2.7rem;
      font-weight: 800;
      letter-spacing: -1.5px;
      line-height: 1.15;
      margin-bottom: 16px;
    }}
    .hero p {{
      font-size: 1.15rem;
      color: var(--text-muted);
      max-width: 840px;
      margin: 0 auto;
    }}
    .section-title {{
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.8px;
      margin: 60px 0 16px 0;
    }}
    .section-sub {{
      color: var(--text-muted);
      font-size: 1.1rem;
      margin-bottom: 32px;
    }}
    .master-frame-box {{
      background: #FFFFFF;
      border: 1px solid var(--surface-border);
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.05);
      margin-bottom: 50px;
    }}
    .master-frame-img {{
      width: 100%;
      border-radius: 16px;
      display: block;
      border: 1px solid var(--surface-border);
    }}
    .sol-card {{
      background: #FFFFFF;
      border: 1px solid var(--surface-border);
      border-radius: 24px;
      padding: 32px;
      margin-bottom: 50px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.04);
      display: grid;
      grid-template-columns: 460px 1fr;
      gap: 36px;
      align-items: start;
    }}
    @media(max-width: 1024px) {{
      .sol-card {{ grid-template-columns: 1fr; }}
    }}
    .sol-frame-img {{
      width: 100%;
      border-radius: 18px;
      border: 2px solid var(--surface-border);
      box-shadow: 0 6px 20px rgba(0,0,0,0.08);
      display: block;
    }}
    .sol-pill {{
      display: inline-block;
      padding: 4px 14px;
      border-radius: 999px;
      color: #FFF;
      font-weight: 800;
      font-size: 0.85rem;
      margin-bottom: 12px;
    }}
    .sol-title {{
      font-size: 1.6rem;
      font-weight: 800;
      color: #0F172A;
      margin-bottom: 10px;
      line-height: 1.25;
    }}
    .method-block {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 16px;
      padding: 20px;
      margin-top: 18px;
    }}
    .method-block h4 {{
      font-size: 0.95rem;
      font-weight: 800;
      color: #0F172A;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .method-block p {{
      font-size: 0.95rem;
      color: #475569;
      line-height: 1.6;
    }}
    .metrics-bar {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-top: 18px;
    }}
    .metric-item {{
      background: #FFFFFF;
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      padding: 12px 14px;
      text-align: center;
    }}
    .metric-val {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--primary);
    }}
    .metric-lbl {{
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 700;
      text-transform: uppercase;
      margin-top: 2px;
    }}
    .frame-tag {{
      background: #FEF3C7;
      color: #92400E;
      font-family: 'JetBrains Mono', monospace;
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.85rem;
      display: inline-block;
      margin-bottom: 14px;
    }}
    .table-container {{
      background: #FFFFFF;
      border: 1px solid var(--surface-border);
      border-radius: 20px;
      overflow-x: auto;
      margin: 30px 0;
      box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      min-width: 850px;
    }}
    th {{
      background: #F8FAFC;
      padding: 16px 18px;
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      border-bottom: 1px solid var(--surface-border);
    }}
    td {{
      padding: 16px 18px;
      border-bottom: 1px solid var(--surface-border);
      font-size: 0.92rem;
    }}
    tr:last-child td {{ border-bottom: none; }}
    .lang-section {{ display: none; }}
    .lang-section.active {{ display: block; }}
  </style>
</head>
<body>

  <nav class="top-nav">
    <div class="brand">
      <span>StairMaster AI Lab</span>
      <span class="brand-badge">Frames & Méthodes</span>
    </div>
    <div class="nav-links">
      <a href="client_presentation_white.html" class="nav-link">← Retour Présentation Executive</a>
      <div class="lang-switch">
        <button class="lang-btn active" id="btn-fr" onclick="switchLang('fr')">🇫🇷 Français</button>
        <button class="lang-btn" id="btn-en" onclick="switchLang('en')">🇬🇧 English</button>
      </div>
    </div>
  </nav>

  <div class="container">

    <!-- ================================================================= -->
    <!-- SECTION FRANÇAISE -->
    <!-- ================================================================= -->
    <div id="section-fr" class="lang-section active">
      <section class="hero">
        <span class="badge badge-primary">🎯 Objectif du Projet & Benchmark de Latence</span>
        <h1>L'Objectif du Projet : Compter les pas en direct, sans erreur et sans retard</h1>
        <p><strong>Le But :</strong> Mesurer automatiquement et en temps réel chaque marche franchie sur le StairMaster (exactement <strong>34 marches en 60 secondes</strong>, soit 34,0 pas/min), avec 100% d'exactitude, zéro retard d'affichage (ultra-faible latence) et un coût matériel minimal.</p>
      </section>

      <!-- BLOC OBJECTIF & BENCHMARK DE LATENCE -->
      <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:16px; padding:24px; margin-bottom:32px;">
        <h3 style="font-size:1.25rem; font-weight:800; color:#0F172A; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
          ⏱️ La Latence de Chaque Solution (Temps de Réaction à l'Écran)
        </h3>
        <p style="color:#64748B; margin-bottom:18px; font-size:0.95rem;">
          La latence est le délai entre le moment où le pied touche la marche et le moment où le compteur s'incrémente à l'écran. Pour une bonne expérience en direct, ce retard doit être inférieur à 0,1 seconde.
        </p>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap:16px;">
          
          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #10B981; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#10B981;">SOLUTION 3 (MACHINE)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">0 ms (Instantané)</div>
            <p style="font-size:0.85rem; color:#64748B;">Traite 60s en <strong>0,37s</strong> (>500 FPS). Calcul embarqué léger, affichage direct sans délai.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #8B5CF6; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#8B5CF6;">SOLUTION 5 (SON / MICRO)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">&lt; 10 ms (Immédiat)</div>
            <p style="font-size:0.85rem; color:#64748B;">Traite 60s en <strong>0,39s</strong>. Analyse acoustique directe par microphone, sans flux vidéo.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #0284C7; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#0284C7;">SOLUTION 2 (SQUELETTE YOLO)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">~15 ms (Temps Réel)</div>
            <p style="font-size:0.85rem; color:#64748B;">Exécution à <strong>72 FPS</strong> sur processeur graphique (Edge GPU) pour suivre les articulations.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #F59E0B; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#F59E0B;">SOLUTION 4 (FUSION CAM+SON)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">100 ms (0,1s)</div>
            <p style="font-size:0.85rem; color:#64748B;">Fenêtre de coïncidence temporelle (100 ms) entre signal optique et acoustique.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #EF4444; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#EF4444;">SOLUTION 1 (IA CLOUD / VLM)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#EF4444; margin:6px 0;">12 secondes (Retard)</div>
            <p style="font-size:0.85rem; color:#64748B;">Latence réseau et traitement par lots distant générant 2 à 5s de décalage.</p>
          </div>

        </div>
      </div>

      <!-- 1. VUE 5-EN-1 SYNCHRONISÉE -->
      <h2 class="section-title">1. Regardez cette image : le 8ème pas (à 15,4 secondes)</h2>
      <p class="section-sub">Cette photo a été prise au moment exact où la personne pose son pied. Les 5 méthodes trouvent exactement la même chose : <strong>34 pas au total</strong>.</p>
      
      <div class="master-frame-box">
        <img src="{b64_all}" alt="Vue 5-en-1 à l'image 462" class="master-frame-img">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px; flex-wrap:wrap; gap:12px;">
          <div>
            <span class="frame-tag">Photo prise à : 15,40 secondes (Image n°462 sur 1 800)</span>
            <p style="color:#64748B; font-size:0.95rem;">Les 5 écrans affichent tous le 8ème pas au même moment.</p>
          </div>
          <span style="font-family:'JetBrains Mono', monospace; font-weight:700; color:#10B981; background:#ECFDF5; padding:6px 14px; border-radius:8px;">✔ Tout le monde est d'accord : 34 Pas</span>
        </div>
      </div>

      <!-- 2. LES 5 SOLUTIONS EN DÉTAIL -->
      <h2 class="section-title">2. Les 5 Solutions expliquées avec des mots simples</h2>
      <p class="section-sub">Pour chaque solution : la photo analysée, le nombre d'images regardées, et la méthode facile à comprendre :</p>

      <!-- CARTE SOLUTION 1 -->
      <div class="sol-card" style="border-left: 6px solid #EF4444;">
        <div>
          <img src="{b64_s1}" alt="Solution 1 Image 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 1 — Image n°462 (15,40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#EF4444;">SOLUTION 1</span>
          <h3 class="sol-title">L'IA sur Internet (comme ChatGPT / GPT-4o)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">180 photos</div>
              <div class="metric-lbl">Envoyées sur Internet</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">12,0s</div>
              <div class="metric-lbl">Temps d'attente total</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#EF4444;">Trop lent (2 à 5s)</div>
              <div class="metric-lbl">Retard en direct</div>
            </div>
          </div>

          <div class="method-block">
            <h4>Comment ça marche ?</h4>
            <p>1. On ne peut pas envoyer toute la vidéo sur Internet, sinon c'est trop lourd et trop cher. On envoie seulement <strong>3 photos par seconde</strong>.<br>
            2. On demande à l'IA : <em>« Regarde ces photos et dis-moi combien de marches la personne a montées »</em>.<br>
            3. L'IA comprend bien la scène, mais elle met <strong>12 secondes à répondre</strong>. C'est beaucoup trop lent : le sportif a déjà fait 15 pas de plus !<br>
            4. <strong>Ce qu'on voit sur la photo :</strong> Le bandeau vert en haut montre que l'IA a bien vu le pied posé (Pas n°8).</p>
          </div>
        </div>
      </div>

      <!-- CARTE SOLUTION 2 -->
      <div class="sol-card" style="border-left: 6px solid #0284C7;">
        <div>
          <img src="{b64_s2}" alt="Solution 2 Image 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 2 — Image n°462 (15,40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#0284C7;">SOLUTION 2</span>
          <h3 class="sol-title">L'IA qui regarde les jambes de la personne (YOLO)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">1 800</div>
              <div class="metric-lbl">Toutes les images regardées</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">24,9s</div>
              <div class="metric-lbl">Temps pour calculer 60s</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#0284C7;">Presque zéro (15 ms)</div>
              <div class="metric-lbl">Retard en direct</div>
            </div>
          </div>

          <div class="method-block">
            <h4>Comment ça marche ?</h4>
            <p>1. Une caméra filme la personne en entier à 30 images par seconde (les 1 800 images sont regardées).<br>
            2. L'ordinateur dessine des points et des lignes de couleur sur les hanches, les genoux et les chevilles.<br>
            3. Quand une cheville descend puis remonte, l'ordinateur compte 1 pas pour cette jambe.<br>
            4. <strong>Ce qu'on voit sur la photo :</strong> Les lignes de couleur sur les jambes. Le compteur affiche séparément les deux jambes : <strong>16 pas jambe gauche / 18 pas jambe droite</strong>.</p>
          </div>
        </div>
      </div>

      <!-- CARTE SOLUTION 3 -->
      <div class="sol-card" style="border-left: 6px solid #10B981;">
        <div>
          <img src="{b64_s3}" alt="Solution 3 Image 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 3 — Image n°462 (15,40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#10B981;">SOLUTION 3</span>
          <h3 class="sol-title">Kymographe Optique Machine (Fente Inférieure)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">1 800</div>
              <div class="metric-lbl">Images analysées (100%)</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">0,37s</div>
              <div class="metric-lbl">Temps de calcul (60s)</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#10B981;">0 ms</div>
              <div class="metric-lbl">Instantané direct</div>
            </div>
          </div>

          <div class="method-block">
            <h4>Comment ça marche ?</h4>
            <p>1. La caméra surveille uniquement la fente mécanique inférieure où les marches descendent dans le châssis, sans cadrer l'utilisateur.<br>
            2. Chaque passage de marche métallique devant le capteur génère une transition optique nette.<br>
            3. 1 cycle complet de marche = 1 pas physique compté, indépendamment des vêtements ou des croisements de jambes.<br>
            4. L'algorithme est exécutable directement sur processeur embarqué sans nécessiter de carte graphique dédiée.<br>
            5. <strong>Ce qu'on voit sur la photo :</strong> Le rectangle vert en bas à droite s'active au moment précis du franchissement (Pas n°8).</p>
          </div>
        </div>
      </div>

      <!-- CARTE SOLUTION 4 -->
      <div class="sol-card" style="border-left: 6px solid #F59E0B;">
        <div>
          <img src="{b64_s4}" alt="Solution 4 Image 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 4 — Image n°462 (15,40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#F59E0B;">SOLUTION 4</span>
          <h3 class="sol-title">Fusion Multimodale Double Capteur (Caméra + Micro)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">Images + Sons</div>
              <div class="metric-lbl">1 800 images + 2,88M sons</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">28,1s</div>
              <div class="metric-lbl">Temps de calcul total</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#D97706;">100 ms</div>
              <div class="metric-lbl">Fenêtre de synchro</div>
            </div>
          </div>

          <div class="method-block">
            <h4>Comment ça marche ?</h4>
            <p>1. On associe les deux capteurs : la caméra qui observe la marche ET le microphone qui capte le signal sonore.<br>
            2. Pour valider 1 pas, le système exige la concordance des deux signaux dans une fenêtre temporelle de 100 ms.<br>
            3. Cette redondance élimine les faux positifs et garantit une certification rigoureuse.<br>
            4. <strong>Ce qu'on voit sur la photo :</strong> L'onde optique de la caméra (en haut) et le signal sonore (en bas) alignés au pas n°8.</p>
          </div>
        </div>
      </div>

      <!-- CARTE SOLUTION 5 -->
      <div class="sol-card" style="border-left: 6px solid #8B5CF6;">
        <div>
          <img src="{b64_s5}" alt="Solution 5 Image 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 5 — Image n°462 (15,40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#8B5CF6;">SOLUTION 5</span>
          <h3 class="sol-title">Détection Acoustique DSP (Par Microphone)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">0 / 2,88M</div>
              <div class="metric-lbl">Flux vidéo non requis</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">0,39s</div>
              <div class="metric-lbl">Temps de calcul (60s)</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#7C3AED;">&lt;10 ms</div>
              <div class="metric-lbl">Réaction immédiate</div>
            </div>
          </div>

          <div class="method-block">
            <h4>Comment ça marche ?</h4>
            <p>1. <strong>Capteur acoustique :</strong> Un microphone placé sous le châssis capte le signal sonore de la machine.<br>
            2. Un filtre passe-bande isole les basses fréquences (60 à 350 Hz) propres à l'impact mécanique du pied.<br>
            3. Chaque pic d'énergie au-delà du seuil d'impact valide un pas physique.<br>
            4. Le traitement offre un temps de réponse immédiat (&lt;10 ms) sans nécessiter de flux vidéo.<br>
            5. <strong>Ce qu'on voit sur la photo :</strong> Le pic d'amplitude vert marque l'instant exact de l'impact mécanique au pas n°8.</p>
          </div>
        </div>
      </div>

    </div>

    <!-- ================================================================= -->
    <!-- SECTION ANGLAISE -->
    <!-- ================================================================= -->
    <div id="section-en" class="lang-section">
      <section class="hero">
        <span class="badge badge-primary">🎯 Project Target & Latency Benchmark</span>
        <h1>Project Target: Real-Time Step Counting with Zero Error & Zero Lag</h1>
        <p><strong>The Core Objective:</strong> Automatically measure and display every single step taken on the StairMaster in real time (exactly <strong>34 steps in 60 seconds</strong>, 34.0 SPM cadence) with 100% accuracy, instant screen response (ultra-low latency), and minimal hardware cost.</p>
      </section>

      <!-- TARGET & LATENCY BENCHMARK BLOCK EN -->
      <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:16px; padding:24px; margin-bottom:32px;">
        <h3 style="font-size:1.25rem; font-weight:800; color:#0F172A; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
          ⏱️ Latency Benchmark for Each Solution (Screen Response Delay)
        </h3>
        <p style="color:#64748B; margin-bottom:18px; font-size:0.95rem;">
          Latency is the delay between the foot hitting the step and the counter incrementing on the display console. For an engaging user experience, this delay must stay under 0.1s.
        </p>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap:16px;">
          
          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #10B981; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#10B981;">SOLUTION 3 (MACHINE)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">0 ms (Instant)</div>
            <p style="font-size:0.85rem; color:#64748B;">Processes 60s in <strong>0.37s</strong> (>500 FPS). Lightweight embedded edge processing, instantaneous response.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #8B5CF6; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#8B5CF6;">SOLUTION 5 (ACOUSTIC / MIC)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">&lt; 10 ms (Immediate)</div>
            <p style="font-size:0.85rem; color:#64748B;">Processes 60s in <strong>0.39s</strong>. Direct acoustic processing from microphone sensor without video stream.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #0284C7; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#0284C7;">SOLUTION 2 (SKELETAL YOLO)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">~15 ms (Real-Time)</div>
            <p style="font-size:0.85rem; color:#64748B;">Infers at <strong>72 FPS</strong> on an edge GPU to track skeletal joint trajectories.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #F59E0B; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#F59E0B;">SOLUTION 4 (DUAL FUSION)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0F172A; margin:6px 0;">100 ms (0.1s)</div>
            <p style="font-size:0.85rem; color:#64748B;">Coincidence validation buffer (100 ms) cross-referencing optical and acoustic signals.</p>
          </div>

          <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #EF4444; border-radius:12px; padding:16px;">
            <div style="font-size:0.8rem; font-weight:700; color:#EF4444;">SOLUTION 1 (CLOUD VLM)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#EF4444; margin:6px 0;">12 seconds (Lag)</div>
            <p style="font-size:0.85rem; color:#64748B;">Cloud network transmission and batch inference introducing 2–5s latency lag.</p>
          </div>

        </div>
      </div>

      <!-- 1. 5-IN-1 SYNCHRONIZED VIEW -->
      <h2 class="section-title">1. The Critical Moment: Frame #462 (Timestamp = 15.40 seconds)</h2>
      <p class="section-sub">This frame captures the exact trigger of <strong>Step #8</strong>. Notice how all 5 streams align to the exact same millisecond :</p>
      
      <div class="master-frame-box">
        <img src="{b64_all}" alt="5-in-1 Synchronized View at Frame 462" class="master-frame-img">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px; flex-wrap:wrap; gap:12px;">
          <div>
            <span class="frame-tag">Extracted Frame: Frame #462 / 1800 (t = 15.40s)</span>
            <p style="color:#64748B; font-size:0.95rem;">5-in-1 synchronized view showing all 5 systems agreeing on step #8 simultaneously.</p>
          </div>
          <span style="font-family:'JetBrains Mono', monospace; font-weight:700; color:#10B981; background:#ECFDF5; padding:6px 14px; border-radius:8px;">✔ 100% Agreement : 34 Steps</span>
        </div>
      </div>

      <!-- 2. THE 5 SOLUTIONS IN DETAIL -->
      <h2 class="section-title">2. All 5 Methods Dissected with Their Key Frame</h2>
      <p class="section-sub">For each solution: the exact frame analyzed, total data processed, and the plain-English method :</p>

      <!-- SOLUTION 1 EN -->
      <div class="sol-card" style="border-left: 6px solid #EF4444;">
        <div>
          <img src="{b64_s1}" alt="Solution 1 Frame 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 1 — Frame #462 (15.40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#EF4444;">SOLUTION 1</span>
          <h3 class="sol-title">Cloud Vision Foundation Model (VLM - GPT-4o-mini)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">~180</div>
              <div class="metric-lbl">Frames Analyzed</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">12.0s</div>
              <div class="metric-lbl">Compute Time</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#EF4444;">2 to 5s</div>
              <div class="metric-lbl">Perceived Lag</div>
            </div>
          </div>

          <div class="method-block">
            <h4>How does the method work?</h4>
            <p>1. Splits the video into <strong>short 3-second sliding windows</strong> (with a 1-second overlap so no step is lost across boundaries).<br>
            2. Samples only <strong>~3 frames per second</strong> (~180 frames total over 60s) to prevent prohibitive cloud API token costs and bandwidth bottlenecks.<br>
            3. Sends these images to GPT-4o with the prompt: <em>"Count the steps climbed by the athlete."</em><br>
            4. <strong>What this frame shows:</strong> The top green banner confirms the VLM detection identifying the athlete mid-stride at Step #8. Total cloud round-trip processing required ~12 seconds.</p>
          </div>
        </div>
      </div>

      <!-- SOLUTION 2 EN -->
      <div class="sol-card" style="border-left: 6px solid #0284C7;">
        <div>
          <img src="{b64_s2}" alt="Solution 2 Frame 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 2 — Frame #462 (15.40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#0284C7;">SOLUTION 2</span>
          <h3 class="sol-title">AI Skeletal Pose Tracking (YOLOv8-Pose)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">1,800</div>
              <div class="metric-lbl">Frames Analyzed (30 FPS)</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">24.9s</div>
              <div class="metric-lbl">Compute Time</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#0284C7;">~15 ms</div>
              <div class="metric-lbl">Real-Time Delay</div>
            </div>
          </div>

          <div class="method-block">
            <h4>How does the method work?</h4>
            <p>1. Evaluates <strong>all 1,800 frames continuously</strong> at ~72 FPS on an edge GPU.<br>
            2. Tracks $(x, y)$ coordinates for hips, knees, and ankles.<br>
            3. When an ankle trajectory reaches maximum depth and reverses upward, a step is logged for that leg.<br>
            4. <strong>What this frame shows:</strong> The color-coded skeletal keypoints and the breakdown: <strong>16 Left / 18 Right</strong>.</p>
          </div>
        </div>
      </div>

      <!-- SOLUTION 3 EN -->
      <div class="sol-card" style="border-left: 6px solid #10B981;">
        <div>
          <img src="{b64_s3}" alt="Solution 3 Frame 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 3 — Frame #462 (15.40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#10B981;">SOLUTION 3</span>
          <h3 class="sol-title">Machine Step Kymograph (Lower Tread Exit)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">1,800</div>
              <div class="metric-lbl">Frames Analyzed (100%)</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">0.37s</div>
              <div class="metric-lbl">Compute Time</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#10B981;">0 ms</div>
              <div class="metric-lbl">Instantaneous</div>
            </div>
          </div>

          <div class="method-block">
            <h4>How does the method work?</h4>
            <p>1. Monitors exclusively the bottom-right mechanical exit slot where metal stairs return into the chassis.<br>
            2. Processes all 1,800 frames at over <strong>500 FPS</strong> on standard embedded hardware.<br>
            3. Mechanical tread descent generates a pure cyclical signal: 1 cycle = 1 physical stair step.<br>
            4. Operates without tracking the athlete's body, remaining immune to clothing, occlusion, and lighting shifts.<br>
            5. <strong>What this frame shows:</strong> The confirmation banner <em>"TREAD STEP TRIGGERED"</em> as the mechanical tread passes (Step #8).</p>
          </div>
        </div>
      </div>

      <!-- SOLUTION 4 EN -->
      <div class="sol-card" style="border-left: 6px solid #F59E0B;">
        <div>
          <img src="{b64_s4}" alt="Solution 4 Frame 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 4 — Frame #462 (15.40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#F59E0B;">SOLUTION 4</span>
          <h3 class="sol-title">Multimodal Dual Fusion (Optical Tread + Acoustic Mic)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">1,800 + 2.88M</div>
              <div class="metric-lbl">Video Frames + Audio</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">28.1s</div>
              <div class="metric-lbl">Compute Time</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#D97706;">100 ms</div>
              <div class="metric-lbl">Sync Window</div>
            </div>
          </div>

          <div class="method-block">
            <h4>How does the method work?</h4>
            <p>1. Combines <strong>all 1,800 video frames</strong> with <strong>2,880,000 audio samples</strong> (48 kHz).<br>
            2. Cross-checks optical tread descent (Solution 3) and acoustic impact (Solution 5).<br>
            3. A step is logged only if both events align within a 100ms coincidence buffer.<br>
            4. This sensor redundancy eliminates false positives for strict competition logging.<br>
            5. <strong>What this frame shows:</strong> The dual coincidence HUD showing the synchronized optical sine wave and audio thud spike.</p>
          </div>
        </div>
      </div>

      <!-- SOLUTION 5 EN -->
      <div class="sol-card" style="border-left: 6px solid #8B5CF6;">
        <div>
          <img src="{b64_s5}" alt="Solution 5 Frame 462" class="sol-frame-img">
          <div style="text-align:center; margin-top:10px;">
            <span class="frame-tag">Solution 5 — Frame #462 (15.40s)</span>
          </div>
        </div>
        <div>
          <span class="sol-pill" style="background:#8B5CF6;">SOLUTION 5</span>
          <h3 class="sol-title">Acoustic Footstrike DSP (Microphone Sensor)</h3>
          
          <div class="metrics-bar">
            <div class="metric-item">
              <div class="metric-val">0 / 2.88M</div>
              <div class="metric-lbl">Video Camera Not Required</div>
            </div>
            <div class="metric-item">
              <div class="metric-val">0.39s</div>
              <div class="metric-lbl">Compute Time</div>
            </div>
            <div class="metric-item">
              <div class="metric-val" style="color:#7C3AED;">&lt;10 ms</div>
              <div class="metric-lbl">Audio Latency</div>
            </div>
          </div>

          <div class="method-block">
            <h4>How does the method work?</h4>
            <p>1. <strong>Acoustic sensor only:</strong> A microphone under the machine chassis captures mechanical acoustic signals in real time.<br>
            2. Applies a 60–350 Hz bandpass filter to isolate the mechanical thud from background gym noise.<br>
            3. Energy envelope detection registers the step instantaneously upon mechanical impact.<br>
            4. Delivers immediate response time (&lt;10 ms) without requiring video stream transmission or storage.<br>
            5. <strong>What this frame shows:</strong> The green waveform peak marking <em>"FOOTSTRIKE IMPACT DETECTED"</em> at Step #8.</p>
          </div>
        </div>
      </div>

    </div>

  </div>

  <script>
    function switchLang(lang) {{
      document.getElementById('section-fr').classList.remove('active');
      document.getElementById('section-en').classList.remove('active');
      document.getElementById('btn-fr').classList.remove('active');
      document.getElementById('btn-en').classList.remove('active');
      
      document.getElementById('section-' + lang).classList.add('active');
      document.getElementById('btn-' + lang).classList.add('active');
    }}
  </script>
</body>
</html>
'''

p1 = os.path.join(ws_dir, 'frames_and_methods.html')
p2 = os.path.join(ws_dir, 'output/frames_and_methods.html')

with open(p1, 'w', encoding='utf-8') as f:
    f.write(html_code)

with open(p2, 'w', encoding='utf-8') as f:
    f.write(html_code)

print(f"Frames & Methods HTML created:\n - {p1} ({len(html_code)} bytes)\n - {p2}")
