/**
 * Zesty Profiles Vault — Jarvis-style stacked folder interface for saved profiles.
 * Gesture-ready: expose ZestyProfilesVault on window for future hand-tracking hooks.
 */
(function (global) {
  const FALLBACK_AVATAR =
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=150&q=80";

  const CATEGORY_COLORS = {
    Hospitality: { accent: "#FF6B35", glow: "rgba(255,107,53,0.45)" },
    Tech: { accent: "#00F0FF", glow: "rgba(0,240,255,0.45)" },
    Creators: { accent: "#B388FF", glow: "rgba(179,136,255,0.45)" },
    Personal: { accent: "#00E676", glow: "rgba(0,230,118,0.4)" },
  };

  let state = {
    vault: null,
    payload: null,
    selectedId: null,
    mode: "detail", // vault | detail
  };

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function showVault() {
    const vault = $("socialVaultView");
    const detail = $("socialDetailView");
    if (vault) vault.hidden = false;
    if (detail) detail.classList.add("vault-hidden");
    state.mode = "vault";
  }

  function showDetail() {
    const vault = $("socialVaultView");
    const detail = $("socialDetailView");
    if (vault) vault.hidden = true;
    if (detail) detail.classList.remove("vault-hidden");
    state.mode = "detail";
  }

  function setStatus(text, color) {
    const el = $("radar-status");
    if (el) {
      el.innerText = text;
      if (color) el.style.color = color;
    }
  }

  function setSource(text) {
    const el = $("radar-source");
    if (el) {
      el.innerText = text;
      el.style.color = "var(--cyan)";
    }
  }

  function buildFolderStack(category, cards, stackIndex) {
    const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.Personal;
    const folder = document.createElement("div");
    folder.className = "vault-folder";
    folder.dataset.category = category;
    folder.dataset.gestureZone = "vault-folder";
    folder.style.setProperty("--folder-accent", colors.accent);
    folder.style.setProperty("--folder-glow", colors.glow);
    folder.style.setProperty("--stack-i", stackIndex);
    folder.innerHTML = `
      <div class="vault-folder-stack">
        <div class="vault-folder-layer l3"></div>
        <div class="vault-folder-layer l2"></div>
        <div class="vault-folder-layer l1"></div>
        <div class="vault-folder-face">
          <div class="vault-folder-tab"></div>
          <div class="vault-folder-label">${escapeHtml(category)}</div>
          <div class="vault-folder-count">${cards.length} profile${cards.length !== 1 ? "s" : ""}</div>
        </div>
      </div>
      <div class="vault-photo-fan"></div>
      <div class="vault-profile-cards"></div>
    `;

    const cardsEl = folder.querySelector(".vault-profile-cards");
    const fanEl = folder.querySelector(".vault-photo-fan");

    cards.forEach((card, i) => {
      const cardEl = document.createElement("button");
      cardEl.type = "button";
      cardEl.className = "vault-profile-card";
      cardEl.dataset.profileId = card.profile_id || "";
      cardEl.dataset.name = card.name || "";
      cardEl.dataset.gestureZone = "vault-profile";
      cardEl.style.setProperty("--card-i", i);
      cardEl.innerHTML = `
        <img class="vault-card-thumb" src="${escapeHtml(card.image_url || FALLBACK_AVATAR)}" alt="">
        <span class="vault-card-name">${escapeHtml(card.name)}</span>
        <span class="vault-card-platform">${escapeHtml((card.platform || "web").toUpperCase())}</span>
      `;
      cardEl.addEventListener("click", (e) => {
        e.stopPropagation();
        openProfileCard(card);
      });
      cardsEl.appendChild(cardEl);

      const fanImg = document.createElement("img");
      fanImg.className = "vault-fan-photo";
      fanImg.src = card.image_url || FALLBACK_AVATAR;
      fanImg.alt = card.name || "";
      fanImg.style.setProperty("--fan-i", i);
      fanEl.appendChild(fanImg);
    });

    folder.addEventListener("click", () => {
      if (cards.length === 1) openProfileCard(cards[0]);
    });

    return folder;
  }

  function renderVault(payload) {
    state.payload = payload;
    const stage = $("socialVaultFolders");
    const meta = $("socialVaultMeta");
    if (!stage) return;

    stage.innerHTML = "";
    const folders = payload?.folders || {};
    const categories = Object.keys(folders);
    if (!categories.length) {
      stage.innerHTML = `<div class="vault-empty">
        <div class="vault-empty-icon">◈</div>
        <div>Vault empty</div>
        <div class="vault-empty-sub">Probe someone, then say "save this profile"</div>
      </div>`;
      if (meta) meta.innerText = "0 PROFILES INDEXED";
      return;
    }

    categories.forEach((cat, i) => {
      stage.appendChild(buildFolderStack(cat, folders[cat], i));
    });
    if (meta) meta.innerText = `${payload.total || 0} PROFILES // ${categories.length} FOLDERS`;
  }

  function openProfileCard(card) {
    if (!card) return;
    state.selectedId = card.profile_id;
    showDetail();
    setSource("SAVED PROFILE VAULT");
    setStatus("LOCKED", "#FF4500");

    const data = {
      target_image_url: card.image_url,
      social_profile: {
        name: card.name,
        username: card.username,
        platform: card.platform,
        bio: card.bio,
        profile_image_url: card.image_url,
        panel_text: card.data?.panel_text || buildQuickPanel(card),
        saved_profile: true,
      },
    };

    if (typeof populateSocialPanelFromProbe === "function") {
      populateSocialPanelFromProbe(data);
    }

    const panel = $("panelSocial");
    if (panel) {
      panel.classList.add("is-visible");
      if (typeof focusZestyPanel === "function") focusZestyPanel("panelSocial");
    }

    if (typeof ZestyEventBus !== "undefined") {
      ZestyEventBus.emit("vault:profile-opened", card);
    }
  }

  function buildQuickPanel(card) {
    return [
      `NAME: ${card.name}`,
      `PLATFORM: ${(card.platform || "web").toUpperCase()}`,
      card.bio ? `\nBIO:\n${card.bio}` : "",
      "\n[SAVED PROFILE — from vault memory]",
    ].join("\n");
  }

  function animateVaultSearch(name, foundId, onComplete) {
    showVault();
    setSource("VAULT SCAN");
    setStatus("SEARCHING", "#00E676");

    const stage = $("socialVaultFolders");
    const scan = $("socialVaultScanLine");
    if (!stage) return;

    const folders = Array.from(stage.querySelectorAll(".vault-folder"));
    let step = 0;

    function clearHighlights() {
      folders.forEach((f) => {
        f.classList.remove("is-scanning", "is-found", "is-missed");
      });
      if (scan) scan.classList.remove("is-active");
    }

    function finish() {
      if (foundId) {
        const matchFolder = folders.find((f) =>
          f.querySelector(`[data-profile-id="${foundId}"]`)
        );
        if (matchFolder) {
          matchFolder.classList.add("is-found");
          const card = matchFolder.querySelector(`[data-profile-id="${foundId}"]`);
          if (card) card.classList.add("is-popped");
        }
        setStatus("MATCH", "#FF4500");
      } else {
        folders.forEach((f) => f.classList.add("is-missed"));
        setStatus("NO MATCH", "#ff4646");
      }
      if (scan) scan.classList.remove("is-active");
      if (onComplete) setTimeout(onComplete, foundId ? 900 : 600);
    }

    if (!folders.length) {
      finish();
      return;
    }

    if (scan) scan.classList.add("is-active");

    const interval = setInterval(() => {
      clearHighlights();
      if (step < folders.length) {
        folders[step].classList.add("is-scanning");
        step += 1;
      } else {
        clearInterval(interval);
        finish();
      }
    }, 280);
  }

  function animateDelete(profileId) {
    const card = document.querySelector(`[data-profile-id="${profileId}"]`);
    if (card) {
      card.classList.add("is-deleting");
      const folder = card.closest(".vault-folder");
      if (folder) folder.classList.add("is-deleting");
    }
  }

  function animateUpdate(profileId) {
    const card = document.querySelector(`[data-profile-id="${profileId}"]`);
    if (card) card.classList.add("is-updating");
    setSource("RE-PROBING PROFILE");
    setStatus("UPDATING", "#00E676");
  }

  function handleResponse(data) {
    const uiMode = data.ui_mode || "";
    const vault = data.vault;

    if (!uiMode && !vault && !data.saved_profiles) return false;

    const panel = $("panelSocial");
    if (panel) {
      setTimeout(() => {
        panel.classList.add("is-visible");
        if (typeof focusZestyPanel === "function") focusZestyPanel("panelSocial");
      }, 50);
    }

    if (uiMode === "vault" || uiMode === "vault_search") {
      renderVault(vault || { total: 0, profiles: [], folders: {} });
      showVault();
      setSource("PROFILE VAULT");
      if (uiMode === "vault_search") {
        animateVaultSearch(data.lookup_name, data.lookup_found ? data.selected_profile_id : null, () => {
          if (data.lookup_found && data.selected_profile_id) {
            const card = (vault?.profiles || []).find(
              (p) => p.profile_id === data.selected_profile_id
            );
            if (card) setTimeout(() => openProfileCard(card), 400);
          }
        });
      } else if (data.profile_action === "delete") {
        animateDelete(data.selected_profile_id);
        setTimeout(() => renderVault(vault), 700);
      } else {
        setStatus("READY", "#00E676");
      }
      return true;
    }

    if (uiMode === "profile_detail") {
      showDetail();
      if (data.profile_action === "update") {
        const photoFrame = $("social-photo-frame");
        if (photoFrame) photoFrame.classList.add("scanning");
        setSource("RE-PROBING PROFILE");
        setStatus("UPDATING", "#00E676");
      }
      if (typeof populateSocialPanelFromProbe === "function") {
        populateSocialPanelFromProbe(data);
      }
      return true;
    }

    if (vault) {
      renderVault(vault);
      showVault();
      return true;
    }

    return false;
  }

  const ZestyProfilesVault = {
    render: renderVault,
    showVault,
    showDetail,
    openProfileCard,
    animateSearch: animateVaultSearch,
    handleResponse,
    getState: () => ({ ...state }),
    /** Gesture-control hook: select profile by id */
    selectProfileById(profileId) {
      const card = (state.payload?.profiles || []).find((p) => p.profile_id === profileId);
      if (card) openProfileCard(card);
    },
    /** Gesture-control hook: return to folder view */
    backToVault() {
      showVault();
    },
  };

  global.ZestyProfilesVault = ZestyProfilesVault;

  if (typeof ZestyEventBus !== "undefined") {
    ZestyEventBus.on("deep-probe:ready", (data) => {
      if (data.ui_mode) return;
      if (data.deep_probe || data.social_profile) showDetail();
    });
  }
})(window);
