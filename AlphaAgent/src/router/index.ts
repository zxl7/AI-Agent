import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router"

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "Home",
    component: () => import("../views/Home.vue"),
    children: [
      { path: "", redirect: "/chat" },
      { path: "chat", name: "Chat", component: () => import("../views/ChatView.vue") },
      { path: "rag", name: "RAG", component: () => import("../views/RAGView.vue") },
      { path: "workflow", name: "Workflow", component: () => import("../views/WorkflowView.vue") },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
