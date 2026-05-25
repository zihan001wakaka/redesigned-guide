const STORAGE_KEYS = {
  messages: "personal_site_messages",
};

const DEFAULT_PROFILE = {
  name: "张子晗",
  title: "产品 / 产品运营方向",
  bio: "上海大学建筑学硕士二年级，具备设计背景、互联网产品相关实习经历与数据分析能力，正在寻找产品或产品运营方向实习机会。",
  avatar: "assets/avatar.jpg",
};

const $ = (selector) => document.querySelector(selector);

const profileName = $("#profileName");
const profileTitle = $("#profileTitle");
const profileBio = $("#profileBio");
const avatarPreview = $("#avatarPreview");
const avatarFallback = $("#avatarFallback");
const portraitRing = $(".portrait-ring");

const mediaGrid = $("#mediaGrid");

const messageForm = $("#messageForm");
const messageList = $("#messageList");
const messageTemplate = $("#messageTemplate");

let messages = loadJSON(STORAGE_KEYS.messages, [
  {
    id: crypto.randomUUID(),
    name: "留言",
    text: "页面很清爽，期待看到更多作品。",
    image: "",
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

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function applyProfile() {
  profileName.textContent = DEFAULT_PROFILE.name;
  profileTitle.textContent = DEFAULT_PROFILE.title;
  profileBio.textContent = DEFAULT_PROFILE.bio;
  avatarFallback.textContent = DEFAULT_PROFILE.name.trim().slice(0, 1);

  avatarPreview.src = DEFAULT_PROFILE.avatar;
  portraitRing.classList.add("has-image");
}

function renderMedia() {
  mediaGrid.innerHTML = "";

  const empty = document.createElement("p");
  empty.className = "empty";
  empty.textContent = "影像内容暂未公开。";
  mediaGrid.append(empty);
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
    const text = node.querySelector(".message-text");
    const image = node.querySelector(".message-image");
    const likeButton = node.querySelector(".like-button");
    const likeCount = likeButton.querySelector("span");
    const time = node.querySelector("time");

    avatar.textContent = message.name.trim().slice(0, 1).toUpperCase();
    name.textContent = message.name;
    text.textContent = message.text;
    if (message.image) {
      image.src = message.image;
      image.alt = "留言图片";
      image.hidden = false;
    } else {
      image.hidden = true;
    }
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

messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(messageForm);
  const text = String(data.get("messageText")).trim();
  const [imageFile] = messageForm.messageImage.files;

  if (!text) return;

  messages = [
    {
      id: crypto.randomUUID(),
      name: "留言",
      text,
      image: imageFile ? await fileToDataURL(imageFile) : "",
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
