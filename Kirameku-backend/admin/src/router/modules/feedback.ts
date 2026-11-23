const Layout = () => import("@/layout/index.vue");

export default {
  path: "/feedback",
  name: "Feedback",
  component: Layout,
  redirect: "/feedback/index",
  meta: { icon: "ri:feedback-line", title: "反馈管理", rank: 6.5 },
  children: [
    {
      path: "/feedback/index",
      name: "FeedbackIndex",
      component: () => import("@/views/feedback/index.vue"),
      meta: { title: "反馈管理" }
    }
  ]
} satisfies RouteConfigsTable;
