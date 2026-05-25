const STORAGE_KEYS = {
  messages: "personal_site_messages",
  visitor: "personal_site_visitor",
};

const SUPABASE_URL = "https://oonobmfexxxtijtoario.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_Lbesp-uIbaRT0R8aV1RATQ_mh1_tEMs";
const SUPABASE_BUCKET = "guestbook-images";
const MESSAGE_TABLE = "guestbook_messages";

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
const visitorName = $("#visitorName");
const visitorAvatar = $("#visitorAvatar");
const messageText = $("#messageText");
const attachmentPreview = $("#attachmentPreview");

const supabaseClient = createSupabaseClient();
let attachedImageFile = null;

let messages = loadJSON(STORAGE_KEYS.messages, [
  {
    id: crypto.randomUUID(),
    nickname: "匿名访客",
    avatarUrl: "",
    text: "页面很清爽，期待看到更多作品。",
    imageUrl: "",
    likes: 3,
    createdAt: new Date().toISOString(),
  },
]);

let visitor = loadJSON(STORAGE_KEYS.visitor, createDefaultVisitor());

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

function createSupabaseClient() {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY || !window.supabase) return null;
  return window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

function createDefaultVisitor() {
  const suffix = Math.floor(1000 + Math.random() * 9000);
  return {
    nickname: `匿名访客${suffix}`,
    avatarUrl: "",
  };
}

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function normalizeMessage(row) {
  return {
    id: row.id,
    nickname: row.nickname || row.name || "匿名访客",
    avatarUrl: row.avatar_url || row.avatarUrl || "",
    text: row.body || row.text || "",
    imageUrl: row.image_url || row.imageUrl || row.image || "",
    likes: Number(row.likes || 0),
    createdAt: row.created_at || row.createdAt || new Date().toISOString(),
  };
}

function messageToLocalRow(message) {
  return {
    id: message.id,
    nickname: message.nickname,
    avatarUrl: message.avatarUrl,
    text: message.text,
    imageUrl: message.imageUrl,
    likes: message.likes,
    createdAt: message.createdAt,
  };
}

function getInitials(name) {
  return (name || "匿名访客").trim().slice(0, 1).toUpperCase();
}

function applyVisitor() {
  visitorName.value = visitor.nickname || "";
  visitorAvatar.value = visitor.avatarUrl || "";
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

async function loadMessages() {
  if (!supabaseClient) {
    renderMessages();
    return;
  }

  const { data, error } = await supabaseClient
    .from(MESSAGE_TABLE)
    .select("id,nickname,avatar_url,body,image_url,likes,created_at")
    .order("created_at", { ascending: false })
    .limit(50);

  if (error) {
    console.warn(error);
    renderMessages();
    return;
  }

  messages = (data || []).map(normalizeMessage);
  renderMessages();
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

    if (message.avatarUrl) {
      const avatarImage = document.createElement("img");
      avatarImage.src = message.avatarUrl;
      avatarImage.alt = "";
      avatar.append(avatarImage);
    } else {
      avatar.textContent = getInitials(message.nickname);
    }
    name.textContent = message.nickname || "匿名访客";
    text.textContent = message.text;
    if (message.imageUrl) {
      image.src = message.imageUrl;
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
      likeCount.textContent = message.likes;
      saveJSON(STORAGE_KEYS.messages, messages.map(messageToLocalRow));

      if (supabaseClient) {
        supabaseClient
          .from(MESSAGE_TABLE)
          .update({ likes: message.likes })
          .eq("id", message.id)
          .then(({ error }) => error && console.warn(error));
      }
    });

    messageList.append(card);
  });
}

function renderAttachmentPreview() {
  attachmentPreview.innerHTML = "";
  attachmentPreview.hidden = !attachedImageFile;

  if (!attachedImageFile) return;

  const image = document.createElement("img");
  image.src = URL.createObjectURL(attachedImageFile);
  image.alt = "待发布图片";

  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "移除图片";
  remove.addEventListener("click", () => {
    attachedImageFile = null;
    renderAttachmentPreview();
  });

  attachmentPreview.append(image, remove);
}

function pickImageFromTransfer(items) {
  const files = [...items]
    .map((item) => (item.kind === "file" ? item.getAsFile() : item))
    .filter(Boolean);
  return files.find((file) => file.type.startsWith("image/")) || null;
}

async function uploadAttachedImage(file) {
  if (!file) return "";

  if (!supabaseClient) {
    return fileToDataURL(file);
  }

  const extension = file.name.split(".").pop() || "jpg";
  const filePath = `${Date.now()}-${crypto.randomUUID()}.${extension}`;
  const { error } = await supabaseClient.storage
    .from(SUPABASE_BUCKET)
    .upload(filePath, file, {
      cacheControl: "3600",
      upsert: false,
      contentType: file.type,
    });

  if (error) throw error;

  const { data } = supabaseClient.storage.from(SUPABASE_BUCKET).getPublicUrl(filePath);
  return data.publicUrl;
}

messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(messageForm);
  const text = String(data.get("messageText")).trim();
  visitor = {
    nickname: String(data.get("visitorName")).trim() || "匿名访客",
    avatarUrl: String(data.get("visitorAvatar")).trim(),
  };
  saveJSON(STORAGE_KEYS.visitor, visitor);

  if (!text) return;

  try {
    const imageUrl = await uploadAttachedImage(attachedImageFile);
    const message = {
      id: crypto.randomUUID(),
      nickname: visitor.nickname,
      avatarUrl: visitor.avatarUrl,
      text,
      imageUrl,
      likes: 0,
      createdAt: new Date().toISOString(),
    };

    if (supabaseClient) {
      const { error } = await supabaseClient.from(MESSAGE_TABLE).insert({
        id: message.id,
        nickname: message.nickname,
        avatar_url: message.avatarUrl,
        body: message.text,
        image_url: message.imageUrl,
        likes: message.likes,
        created_at: message.createdAt,
      });

      if (error) throw error;
    }

    messages = [message, ...messages];
    saveJSON(STORAGE_KEYS.messages, messages.map(messageToLocalRow));
    messageForm.reset();
    applyVisitor();
    attachedImageFile = null;
    renderAttachmentPreview();
    renderMessages();
  } catch (error) {
    console.warn(error);
    alert("留言发布失败，请稍后再试。");
  }
});

messageText.addEventListener("paste", (event) => {
  const image = pickImageFromTransfer(event.clipboardData.items);
  if (!image) return;
  attachedImageFile = image;
  renderAttachmentPreview();
});

messageText.addEventListener("dragover", (event) => {
  event.preventDefault();
});

messageText.addEventListener("drop", (event) => {
  event.preventDefault();
  const image = pickImageFromTransfer(event.dataTransfer.items);
  if (!image) return;
  attachedImageFile = image;
  renderAttachmentPreview();
});

applyProfile();
applyVisitor();
renderMedia();
messages = messages.map(normalizeMessage);
loadMessages();
