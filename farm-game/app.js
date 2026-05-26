const STORAGE_KEY = "farm_game_mvp_save_v3";

const CROPS = {
  wheat: {
    id: "wheat",
    name: "小麦",
    icon: "🌾",
    seedPrice: 10,
    growMs: 30_000,
    sellPrice: 18,
    xp: 8,
  },
  carrot: {
    id: "carrot",
    name: "胡萝卜",
    icon: "🥕",
    seedPrice: 20,
    growMs: 60_000,
    sellPrice: 38,
    xp: 16,
  },
  tomato: {
    id: "tomato",
    name: "番茄",
    icon: "🍅",
    seedPrice: 35,
    growMs: 120_000,
    sellPrice: 70,
    xp: 30,
  },
};

const QUEST_TARGET = 6;
const LEVEL_BASE_XP = 100;
const MAX_LEVEL = 10;

const $ = (selector) => document.querySelector(selector);

const coins = $("#coins");
const cropCount = $("#cropCount");
const harvestCount = $("#harvestCount");
const playerLevel = $("#playerLevel");
const xpFill = $("#xpFill");
const xpText = $("#xpText");
const farmGrid = $("#farmGrid");
const shopList = $("#shopList");
const seedBagList = $("#seedBagList");
const warehouseList = $("#warehouseList");
const actionHint = $("#actionHint");
const selectedSeedText = $("#selectedSeedText");
const questText = $("#questText");
const questState = $("#questState");
const toast = $("#toast");
const plotTemplate = $("#plotTemplate");
const shopTemplate = $("#shopTemplate");
const bagTemplate = $("#bagTemplate");
const quantityModal = $("#quantityModal");
const modalTitle = $("#modalTitle");
const modalDesc = $("#modalDesc");
const modalClose = $("#modalClose");
const quantityOptions = $("#quantityOptions");
const modalSummary = $("#modalSummary");
const modalConfirm = $("#modalConfirm");

let state = loadState();
let toastTimer = 0;
let selectedSeedId = null;
let pendingTransaction = null;
let selectedQuantity = 1;

function createInitialState() {
  return {
    coins: 1000,
    plots: Array.from({ length: 6 }, () => ({
      cropId: null,
      plantedAt: null,
    })),
    bag: {
      seeds: {
        wheat: 0,
        carrot: 0,
        tomato: 0,
      },
      crops: {
        wheat: 0,
        carrot: 0,
        tomato: 0,
      },
    },
    stats: {
      harvested: 0,
      xp: 0,
    },
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return createInitialState();
    return normalizeState(JSON.parse(raw));
  } catch {
    return createInitialState();
  }
}

function normalizeState(saved) {
  const initial = createInitialState();
  const state = {
    ...initial,
    ...saved,
    bag: {
      seeds: {
        ...initial.bag.seeds,
        ...saved?.bag?.seeds,
      },
      crops: {
        ...initial.bag.crops,
        ...saved?.bag?.crops,
      },
    },
    stats: {
      ...initial.stats,
      ...saved?.stats,
    },
  };

  if (!Array.isArray(state.plots) || state.plots.length !== 6) {
    state.plots = initial.plots;
  }

  Object.keys(CROPS).forEach((id) => {
    state.bag.seeds[id] = Number(state.bag.seeds[id]) || 0;
    state.bag.crops[id] = Number(state.bag.crops[id]) || 0;
  });

  const coins = Number(state.coins);
  const harvested = Number(state.stats.harvested);
  const xp = Number(state.stats.xp);
  state.coins = Number.isFinite(coins) ? coins : initial.coins;
  state.stats.harvested = Number.isFinite(harvested) ? harvested : 0;
  state.stats.xp = Number.isFinite(xp) ? xp : 0;
  state.plots = state.plots.map((plot) => {
    if (!plot?.cropId || !CROPS[plot.cropId]) {
      return { cropId: null, plantedAt: null };
    }

    const plantedAt = Number(plot.plantedAt);
    return {
      cropId: plot.cropId,
      plantedAt: Number.isFinite(plantedAt) ? plantedAt : Date.now(),
    };
  });
  return state;
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    showToast("当前浏览器没有写入本地存档，但本次操作已生效。");
  }
}

function formatTime(ms) {
  const seconds = Math.max(0, Math.ceil(ms / 1000));
  if (seconds < 60) return `${seconds} 秒`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest ? `${minutes}分${rest}秒` : `${minutes} 分`;
}

function getPlotStatus(plot) {
  if (!plot.cropId) {
    return {
      status: "empty",
      progress: 0,
      remaining: 0,
      ready: false,
    };
  }

  const crop = CROPS[plot.cropId];
  const elapsed = Date.now() - plot.plantedAt;
  const progress = Math.min(1, elapsed / crop.growMs);
  return {
    status: progress >= 1 ? "ready" : "growing",
    progress,
    remaining: crop.growMs - elapsed,
    ready: progress >= 1,
  };
}

function getTotalCrops() {
  return Object.values(state.bag.crops).reduce((sum, value) => sum + value, 0);
}

function getMaxLevelXp() {
  let total = 0;
  for (let level = 1; level < MAX_LEVEL; level += 1) {
    total += LEVEL_BASE_XP + (level - 1) * 50;
  }
  return total;
}

function getPlayerProgress() {
  const maxLevelXp = getMaxLevelXp();
  const totalXp = Math.min(state.stats.xp, maxLevelXp);
  let level = 1;
  let remainingXp = totalXp;
  let nextLevelXp = LEVEL_BASE_XP;

  while (level < MAX_LEVEL && remainingXp >= nextLevelXp) {
    remainingXp -= nextLevelXp;
    level += 1;
    nextLevelXp = LEVEL_BASE_XP + (level - 1) * 50;
  }

  const isMax = level >= MAX_LEVEL;
  return {
    level,
    currentXp: isMax ? nextLevelXp : remainingXp,
    nextLevelXp,
    percent: isMax ? 100 : Math.min(100, Math.round((remainingXp / nextLevelXp) * 100)),
    totalXp,
    isMax,
  };
}

function showToast(message) {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("show");
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1800);
}

function openPanel(panelId) {
  document.querySelectorAll("[data-panel-content]").forEach((panel) => {
    const isActive = panel.id === panelId;
    panel.hidden = !isActive;
    panel.classList.toggle("active", isActive);
  });

  document.querySelectorAll(".tool-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.panel === panelId);
  });
}

function openQuantityModal(type, cropId) {
  const crop = CROPS[cropId];
  pendingTransaction = { type, cropId };
  selectedQuantity = 1;
  quantityOptions.innerHTML = "";
  modalTitle.textContent = type === "buy" ? `购买${crop.name}种子` : `出售${crop.name}`;
  modalDesc.textContent =
    type === "buy"
      ? `单价 ${crop.seedPrice} 金币，选择购买数量。`
      : `单价 ${crop.sellPrice} 金币，选择出售数量。`;

  for (let quantity = 1; quantity <= 10; quantity += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = quantity;
    button.dataset.quantity = String(quantity);
    button.addEventListener("click", () => selectQuantity(quantity));
    quantityOptions.append(button);
  }

  renderQuantityModal();
  quantityModal.hidden = false;
  quantityModal.removeAttribute("hidden");
  quantityModal.classList.remove("is-closed");
  quantityModal.classList.add("open");
  quantityModal.style.display = "grid";
}

function closeQuantityModal() {
  quantityModal.classList.remove("open");
  quantityModal.classList.add("is-closed");
  quantityModal.hidden = true;
  quantityModal.setAttribute("hidden", "");
  quantityModal.style.display = "none";
  pendingTransaction = null;
}

function selectQuantity(quantity) {
  selectedQuantity = quantity;
  renderQuantityModal();
}

function renderQuantityModal() {
  if (!pendingTransaction) return;

  const crop = CROPS[pendingTransaction.cropId];
  const price = pendingTransaction.type === "buy" ? crop.seedPrice : crop.sellPrice;
  const action = pendingTransaction.type === "buy" ? "购买" : "出售";
  modalSummary.textContent = `已选 ${selectedQuantity} · ${action}总额 ${price * selectedQuantity} 金币`;

  quantityOptions.querySelectorAll("button").forEach((button) => {
    const isSelected = Number(button.dataset.quantity) === selectedQuantity;
    button.classList.toggle("selected", isSelected);
  });
}

function confirmQuantity() {
  if (!pendingTransaction) return;

  const { type, cropId } = pendingTransaction;
  const crop = CROPS[cropId];
  const quantity = selectedQuantity;

  if (type === "buy") {
    const totalPrice = crop.seedPrice * quantity;
    if (state.coins < totalPrice) {
      showToast(`金币不足，需要 ${totalPrice} 金币。`);
      return;
    }

    state.coins -= totalPrice;
    state.bag.seeds[cropId] += quantity;
    closeQuantityModal();
    saveState();
    render();
    showToast(`购买成功：${quantity} 个${crop.name}种子`);
    return;
  }

  if (state.bag.crops[cropId] < quantity) {
    showToast(`${crop.name}库存不足。`);
    return;
  }

  state.bag.crops[cropId] -= quantity;
  state.coins += crop.sellPrice * quantity;
  closeQuantityModal();
  saveState();
  render();
  showToast(`出售成功：${quantity} 个${crop.name}，获得 ${crop.sellPrice * quantity} 金币`);
}

function buySeed(cropId, quantity = 1) {
  const crop = CROPS[cropId];
  const totalPrice = crop.seedPrice * quantity;
  if (state.coins < totalPrice) {
    showToast(`金币不足，需要 ${totalPrice} 金币。`);
    return false;
  }

  state.coins -= totalPrice;
  state.bag.seeds[cropId] += quantity;
  saveState();
  return true;
}

function sellCrop(cropId, quantity = 1) {
  const crop = CROPS[cropId];
  if (state.bag.crops[cropId] < quantity) {
    showToast(`${crop.name}库存不足。`);
    return false;
  }

  state.bag.crops[cropId] -= quantity;
  state.coins += crop.sellPrice * quantity;
  saveState();
  return true;
}

function selectSeed(cropId) {
  if (state.bag.seeds[cropId] <= 0) {
    showToast("这个种子数量为 0，先去商店购买。");
    return;
  }

  if (selectedSeedId === cropId) {
    selectedSeedId = null;
    render();
    showToast(`已取消选择${CROPS[cropId].name}种子`);
    return;
  }

  selectedSeedId = cropId;
  render();
  showToast(`已选择${CROPS[cropId].name}种子，点击空地播种。`);
}

function plantSeed(plotIndex) {
  const plot = state.plots[plotIndex];
  if (plot.cropId) return false;

  if (!selectedSeedId) {
    openPanel("bagPanel");
    showToast("请先在背包里选择一种种子。");
    return false;
  }

  if (state.bag.seeds[selectedSeedId] <= 0) {
    selectedSeedId = null;
    render();
    openPanel("bagPanel");
    showToast("这个种子已经用完了，请重新选择。");
    return false;
  }

  const cropId = selectedSeedId;
  state.bag.seeds[cropId] -= 1;
  state.plots[plotIndex] = {
    cropId,
    plantedAt: Date.now(),
  };

  if (state.bag.seeds[cropId] <= 0) {
    selectedSeedId = null;
  }

  saveState();
  render();
  showToast(`种下${CROPS[cropId].name}`);
  return true;
}

function harvestPlot(plotIndex) {
  const plot = state.plots[plotIndex];
  if (!plot.cropId) return;

  const crop = CROPS[plot.cropId];
  const status = getPlotStatus(plot);
  if (!status.ready) {
    showToast(`${crop.name}还需要 ${formatTime(status.remaining)}`);
    return;
  }

  state.bag.crops[crop.id] += 1;
  state.stats.harvested += 1;
  state.stats.xp += crop.xp;
  const progress = getPlayerProgress();
  if (progress.isMax) {
    state.stats.xp = getMaxLevelXp();
  }
  state.plots[plotIndex] = {
    cropId: null,
    plantedAt: null,
  };
  saveState();
  render();
  showToast(progress.isMax ? `收获 1 个${crop.name}，等级已满` : `收获 1 个${crop.name}，获得 ${crop.xp} 经验`);
}

function renderFarm() {
  farmGrid.innerHTML = "";

  state.plots.forEach((plot, index) => {
    const node = plotTemplate.content.cloneNode(true);
    const button = node.querySelector(".plot");
    const icon = node.querySelector(".plot-icon");
    const title = node.querySelector(".plot-title");
    const time = node.querySelector(".plot-time");
    const progress = node.querySelector(".plot-progress i");
    const dot = node.querySelector(".ready-dot");
    const status = getPlotStatus(plot);

    button.classList.add(status.status);
    progress.style.width = `${status.ready ? 100 : Math.round(status.progress * 100)}%`;
    dot.hidden = !status.ready;

    if (!plot.cropId) {
      icon.textContent = "+";
      title.textContent = "空地";
      time.textContent = selectedSeedId ? `种${CROPS[selectedSeedId].name}` : "先选种子";
      button.addEventListener("click", () => plantSeed(index));
    } else {
      const crop = CROPS[plot.cropId];
      icon.textContent = crop.icon;
      title.textContent = status.ready ? `${crop.name}可收获` : `${crop.name}生长中`;
      time.textContent = status.ready ? "点击收获" : `剩余 ${formatTime(status.remaining)}`;
      button.addEventListener("click", () => harvestPlot(index));
    }

    farmGrid.append(button);
  });
}

function renderShop() {
  shopList.innerHTML = "";

  Object.values(CROPS).forEach((crop) => {
    const node = shopTemplate.content.cloneNode(true);
    node.querySelector(".crop-icon").textContent = crop.icon;
    node.querySelector(".crop-name").textContent = `${crop.name}种子`;
    node.querySelector(".crop-meta").textContent = `${crop.seedPrice} 金币 · ${formatTime(crop.growMs)}成熟`;
    const button = node.querySelector("button");
    button.textContent = "购买";
    button.addEventListener("click", () => openQuantityModal("buy", crop.id));
    shopList.append(node);
  });
}

function renderSeedBag() {
  seedBagList.innerHTML = "";
  if (selectedSeedId && state.bag.seeds[selectedSeedId] <= 0) {
    selectedSeedId = null;
  }
  selectedSeedText.textContent = selectedSeedId ? `已选择：${CROPS[selectedSeedId].name}` : "未选择种子";

  Object.values(CROPS).forEach((crop) => {
    const seedNode = bagTemplate.content.cloneNode(true);
    const item = seedNode.querySelector(".bag-item");
    seedNode.querySelector(".crop-icon").textContent = crop.icon;
    seedNode.querySelector(".bag-name").textContent = `${crop.name}种子`;
    seedNode.querySelector(".bag-meta").textContent = `数量 ${state.bag.seeds[crop.id]}`;
    const seedButton = seedNode.querySelector("button");
    const isSelected = selectedSeedId === crop.id;
    item.classList.toggle("selected", isSelected);
    seedButton.textContent = isSelected ? "取消" : "选择";
    seedButton.disabled = !state.bag.seeds[crop.id];
    seedButton.addEventListener("click", () => selectSeed(crop.id));
    seedBagList.append(seedNode);
  });
}

function renderWarehouse() {
  warehouseList.innerHTML = "";

  Object.values(CROPS).forEach((crop) => {
    const cropNode = bagTemplate.content.cloneNode(true);
    cropNode.querySelector(".crop-icon").textContent = crop.icon;
    cropNode.querySelector(".bag-name").textContent = `${crop.name}`;
    cropNode.querySelector(".bag-meta").textContent = `数量 ${state.bag.crops[crop.id]} · 售价 ${crop.sellPrice}`;
    const cropButton = cropNode.querySelector("button");
    cropButton.textContent = "售卖";
    cropButton.classList.add("sell");
    cropButton.disabled = !state.bag.crops[crop.id];
    cropButton.addEventListener("click", () => openQuantityModal("sell", crop.id));
    warehouseList.append(cropNode);
  });
}

function renderQuest() {
  const done = Math.min(state.stats.harvested, QUEST_TARGET);
  questText.textContent = `收获 ${QUEST_TARGET} 个作物：${done}/${QUEST_TARGET}。完成后说明基础种植闭环已经跑通。`;
  questState.textContent = done >= QUEST_TARGET ? "已完成" : "进行中";
  actionHint.textContent = selectedSeedId
    ? `已选择${CROPS[selectedSeedId].name}种子，点击空地完成播种。`
    : "先打开背包选择种子，再点击空地播种。";
}

function renderStats() {
  const progress = getPlayerProgress();
  coins.textContent = state.coins;
  cropCount.textContent = getTotalCrops();
  harvestCount.textContent = state.stats.harvested;
  playerLevel.textContent = progress.isMax ? "MAX" : `lv.${progress.level}`;
  playerLevel.classList.toggle("max", progress.isMax);
  xpFill.style.width = `${progress.percent}%`;
  xpText.textContent = progress.isMax ? `lv.${MAX_LEVEL} 满级` : `${progress.currentXp} / ${progress.nextLevelXp} 经验`;
}

function render() {
  renderStats();
  renderFarm();
  renderShop();
  renderSeedBag();
  renderWarehouse();
  renderQuest();
}

document.querySelectorAll(".tool-button").forEach((button) => {
  button.addEventListener("click", () => openPanel(button.dataset.panel));
});

modalClose.addEventListener("click", closeQuantityModal);
modalConfirm.addEventListener("click", (event) => {
  event.preventDefault();
  confirmQuantity();
});
quantityModal.addEventListener("click", (event) => {
  if (event.target === quantityModal) closeQuantityModal();
});

setInterval(() => {
  render();
}, 1000);

render();
