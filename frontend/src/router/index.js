import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '../views/DashboardView.vue';

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView
  },
  {
    path: '/events',
    name: 'events',
    component: () => import('../views/EventsView.vue')
  },
  {
    path: '/detections',
    name: 'detections',
    component: () => import('../views/DetectionsView.vue')
  },
  {
    path: '/ask',
    name: 'ask',
    component: () => import('../views/AskView.vue')
  },
  {
    path: '/agents',
    name: 'agents',
    component: () => import('../views/AgentsView.vue')
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

export default router;
