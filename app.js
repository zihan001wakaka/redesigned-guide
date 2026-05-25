const STORAGE_KEYS = {
  profile: "personal_site_profile",
  profileVersion: "personal_site_profile_version",
  media: "personal_site_media",
  messages: "personal_site_messages",
};

const CURRENT_PROFILE_VERSION = "2026-05-25-zhang-zihan";
const DEFAULT_PROFILE = {
  name: "张子晗",
  title: "产品 / 产品运营方向",
  bio: "上海大学建筑学硕士二年级，具备设计背景、互联网产品相关实习经历与数据分析能力，正在寻找产品或产品运营方向实习机会。",
  avatar: "assets/avatar.jpg",
};

const $ = (selector) => document.querySelector(selector);

const profileForm = $("#profileForm");
const nameInput = $("#nameInput");
const titleInput = $("#titleInput");
const bioInput = $("#bioInput");
const avatarInput = $("#avatarInput");
const profileName = $("#profileName");
const profileTitle = $("#profileTitle");
const profileBio = $("#profileBio");
const avatarPreview = $("#avatarPreview");
const avatarFallback = $("#avatarFallback");
const portraitRing = $(".portrait-ring");

const mediaInput = $("#mediaInput");
const mediaGrid = $("#mediaGrid");
const clearMedia = $("#clearMedia");
const mediaTemplate = $("#mediaTemplate");

const messageForm = $("#messageForm");
const messageList = $("#messageList");
const messageTemplate = $("#messageTemplate");

let profile = loadProfile();

let mediaItems = loadJSON(STORAGE_KEYS.media, []);
let messages = loadJSON(STORAGE_KEYS.messages, [
  {
    id: crypto.randomUUID(),
    name: "访客",
    mood: "来打招呼",
    text: "页面很清爽，期待看到更多作品。",
    likes: 3,
    createdAt: new Date().toISOString(),
  },
]);

function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function loadProfile() {
  const savedVersion = localStorage.getItem(STORAGE_KEYS.profileVersion);
  if (savedVersion !== CURRENT_PROFILE_VERSION) {
    saveJSON(STORAGE_KEYS.profile, DEFAULT_PROFILE);
    localStorage.setItem(STORAGE_KEYS.profileVersion, CURRENT_PROFILE_VERSION);
    return { ...DEFAULT_PROFILE };
  }

  return loadJSON(STORAGE_KEYS.profile, DEFAULT_PROFILE);
}

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function applyProfile() {
  profileName.textContent = profile.name || DEFAULT_PROFILE.name;
  profileTitle.textContent = profile.title || "";
  profileBio.textContent = profile.bio || "";
  nameInput.value = profile.name || "";
  titleInput.value = profile.title || "";
  bioInput.value = profile.bio || "";
  avatarFallback.textContent = (profile.name || DEFAULT_PROFILE.name).trim().slice(0, 1);

  if (profile.avatar) {
    avatarPreview.src = profile.avatar;
    portraitRing.classList.add("has-image");
  } else {
    avatarPreview.removeAttribute("src");
    portraitRing.classList.remove("has-image");
  }
}

function renderMedia() {
  mediaGrid.innerHTML = "";

  if (!mediaItems.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "还没有上传内容。";
    mediaGrid.append(empty);
    return;
  }

  mediaItems.forEach((item) => {
    const node = mediaTemplate.content.cloneNode(true);
    const card = node.querySelector(".media-card");
    const shell = node.querySelector(".media-shell");
    const name = node.querySelector(".media-name");
    const remove = node.querySelector(".remove-media");

    const element = document.createElement(item.type.startsWith("video/") ? "video" : "img");
    element.src = item.src;
    element.alt = item.name;
    if (element.tagName === "VIDEO") {
      element.controls = true;
      element.playsInline = true;
    }

    shell.append(element);
    name.textContent = item.name;
    remove.addEventListener("click", () => {
      mediaItems = mediaItems.filter((media) => media.id !== item.id);
      saveJSON(STORAGE_KEYS.media, mediaItems);
      renderMedia();
    });

    mediaGrid.append(card);
  });
}

function renderMessages() {
  messageList.innerHTML = "";

  if (!messages.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "还没有留言。";
    messageList.append(empty);
    return;
  }

  messages.forEach((message) => {
    const node = messageTemplate.content.cloneNode(true);
    const card = node.querySelector(".message-card");
    const avatar = node.querySelector(".message-avatar");
    const name = node.querySelector(".message-name");
    const mood = node.querySelector(".message-mood");
    const text = node.querySelector(".message-text");
    const likeButton = node.querySelector(".like-button");
    const likeCount = likeButton.querySelector("span");
    const time = node.querySelector("time");

    avatar.textContent = message.name.trim().slice(0, 1).toUpperCase();
    name.textContent = message.name;
    mood.textContent = message.mood;
    text.textContent = message.text;
    likeCount.textContent = message.likes;
    time.dateTime = message.createdAt;
    time.textContent = new Intl.DateTimeFormat("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(message.createdAt));

    likeButton.addEventListener("click", () => {
      message.likes += 1;
      saveJSON(STORAGE_KEYS.messages, messages);
      likeCount.textContent = message.likes;
    });

    messageList.append(card);
  });
}

profileForm.addEventListener("submit", (event) => {
  event.preventDefault();
  profile = {
    ...profile,
    name: nameInput.value.trim() || DEFAULT_PROFILE.name,
    title: titleInput.value.trim(),
    bio: bioInput.value.trim(),
  };
  saveJSON(STORAGE_KEYS.profile, profile);
  applyProfile();
});

avatarInput.addEventListener("change", async () => {
  const [file] = avatarInput.files;
  if (!file) return;
  profile.avatar = await fileToDataURL(file);
  saveJSON(STORAGE_KEYS.profile, profile);
  applyProfile();
});

mediaInput.addEventListener("change", async () => {
  const files = [...mediaInput.files];
  const additions = await Promise.all(
    files.map(async (file) => ({
      id: crypto.randomUUID(),
      name: file.name,
      type: file.type,
      src: await fileToDataURL(file),
    }))
  );

  mediaItems = [...additions, ...mediaItems].slice(0, 18);
  saveJSON(STORAGE_KEYS.media, mediaItems);
  renderMedia();
  mediaInput.value = "";
});

clearMedia.addEventListener("click", () => {
  mediaItems = [];
  saveJSON(STORAGE_KEYS.media, mediaItems);
  renderMedia();
});

messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(messageForm);
  const text = String(data.get("messageText")).trim();
  const name = String(data.get("visitorName")).trim();

  if (!text || !name) return;

  messages = [
    {
      id: crypto.randomUUID(),
      name,
      mood: String(data.get("visitorMood")),
      text,
      likes: 0,
      createdAt: new Date().toISOString(),
    },
    ...messages,
  ];
  saveJSON(STORAGE_KEYS.messages, messages);
  messageForm.reset();
  renderMessages();
});

applyProfile();
renderMedia();
renderMessages();
