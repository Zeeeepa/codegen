import { Router } from 'express';
const router = Router();

// TODO: Implement template CRUD routes
router.get('/', (_req, res) => res.json([]));
router.post('/', (_req, res) => res.status(501).json({ error: 'Not implemented' }));

export default router;
