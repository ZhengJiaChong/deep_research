/**
 * SQLite数据库服务 - 历史对话管理
 */

import { openDB } from 'idb'

const DB_NAME = 'deep_research_db'
const DB_VERSION = 1
const STORE_NAME = 'chat_history'

let db = null

// 初始化数据库
export const initDB = async () => {
  if (db) return db
  
  db = await openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      // 创建历史对话存储
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true })
        store.createIndex('timestamp', 'timestamp')
        store.createIndex('researchId', 'researchId')
      }
    }
  })
  
  return db
}

// 保存对话到数据库
export const saveChatToDB = async (chatData) => {
  const database = await initDB()
  
  const chat = {
    query: chatData.query,
    researchId: chatData.researchId,
    messages: chatData.messages,
    timestamp: chatData.timestamp || new Date().toISOString(),
    createdAt: new Date().toISOString()
  }
  
  const id = await database.add(STORE_NAME, chat)
  return id
}

// 获取所有历史对话
export const getAllChats = async () => {
  const database = await initDB()
  const index = database.transaction(STORE_NAME).store.index('timestamp')
  
  // 按时间倒序获取
  const allChats = await index.getAll()
  return allChats.reverse()
}

// 根据ID获取对话
export const getChatById = async (id) => {
  const database = await initDB()
  return await database.get(STORE_NAME, id)
}

// 更新对话
export const updateChat = async (id, updates) => {
  const database = await initDB()
  const chat = await database.get(STORE_NAME, id)
  
  if (chat) {
    const updatedChat = { ...chat, ...updates }
    await database.put(STORE_NAME, updatedChat)
    return updatedChat
  }
  
  return null
}

// 删除对话
export const deleteChat = async (id) => {
  const database = await initDB()
  await database.delete(STORE_NAME, id)
}

// 清空所有历史
export const clearAllChats = async () => {
  const database = await initDB()
  await database.clear(STORE_NAME)
}

// 限制历史记录数量（保留最近N条）
export const limitHistory = async (maxCount = 50) => {
  const database = await initDB()
  const allChats = await getAllChats()
  
  if (allChats.length > maxCount) {
    // 删除最旧的记录
    const toDelete = allChats.slice(maxCount)
    for (const chat of toDelete) {
      await database.delete(STORE_NAME, chat.id)
    }
  }
}
