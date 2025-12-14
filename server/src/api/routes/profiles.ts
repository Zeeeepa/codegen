import { Router, Request, Response } from 'express';
import { prisma } from '../../index';
import { CreateProfileSchema, UpdateProfileSchema } from '../../types';

const router = Router();

// GET /api/profiles - List all profiles
router.get('/', async (_req: Request, res: Response) => {
  try {
    const profiles = await prisma.profile.findMany({
      include: {
        profileTools: true,
        profileMcpTools: { include: { mcpTool: true } },
        profileSkills: { include: { skill: true } },
        profileTemplates: { include: { template: true } },
        sandboxes: true
      },
      orderBy: { createdAt: 'desc' }
    });
    res.json(profiles);
  } catch (error) {
    console.error('Error fetching profiles:', error);
    res.status(500).json({ error: 'Failed to fetch profiles' });
  }
});

// GET /api/profiles/:id - Get single profile
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const profile = await prisma.profile.findUnique({
      where: { id: req.params.id },
      include: {
        profileTools: true,
        profileMcpTools: { include: { mcpTool: true } },
        profileSkills: { include: { skill: true } },
        profileTemplates: { include: { template: true } },
        sandboxes: true
      }
    });
    
    if (!profile) {
      return res.status(404).json({ error: 'Profile not found' });
    }
    
    res.json(profile);
  } catch (error) {
    console.error('Error fetching profile:', error);
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});

// POST /api/profiles - Create profile
router.post('/', async (req: Request, res: Response) => {
  try {
    const data = CreateProfileSchema.parse(req.body);
    
    const profile = await prisma.profile.create({
      data,
      include: {
        profileTools: true,
        profileMcpTools: { include: { mcpTool: true } },
        profileSkills: { include: { skill: true } },
        profileTemplates: { include: { template: true } },
        sandboxes: true
      }
    });
    
    res.status(201).json(profile);
  } catch (error) {
    console.error('Error creating profile:', error);
    res.status(400).json({ error: 'Invalid profile data', details: error });
  }
});

// PUT /api/profiles/:id - Update profile
router.put('/:id', async (req: Request, res: Response) => {
  try {
    const data = UpdateProfileSchema.parse(req.body);
    
    const profile = await prisma.profile.update({
      where: { id: req.params.id },
      data,
      include: {
        profileTools: true,
        profileMcpTools: { include: { mcpTool: true } },
        profileSkills: { include: { skill: true } },
        profileTemplates: { include: { template: true } },
        sandboxes: true
      }
    });
    
    res.json(profile);
  } catch (error) {
    console.error('Error updating profile:', error);
    res.status(400).json({ error: 'Failed to update profile', details: error });
  }
});

// DELETE /api/profiles/:id - Delete profile
router.delete('/:id', async (req: Request, res: Response) => {
  try {
    await prisma.profile.delete({
      where: { id: req.params.id }
    });
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting profile:', error);
    res.status(500).json({ error: 'Failed to delete profile' });
  }
});

// GET /api/profiles/active - Get active profile
router.get('/active/current', async (_req: Request, res: Response) => {
  try {
    const profile = await prisma.profile.findFirst({
      where: { isActive: true },
      include: {
        profileTools: true,
        profileMcpTools: { include: { mcpTool: true } },
        profileSkills: { include: { skill: true } },
        profileTemplates: { include: { template: true } },
        sandboxes: true
      }
    });
    
    if (!profile) {
      return res.status(404).json({ error: 'No active profile found' });
    }
    
    res.json(profile);
  } catch (error) {
    console.error('Error fetching active profile:', error);
    res.status(500).json({ error: 'Failed to fetch active profile' });
  }
});

// POST /api/profiles/:id/activate - Set as active profile
router.post('/:id/activate', async (req: Request, res: Response) => {
  try {
    // Deactivate all profiles
    await prisma.profile.updateMany({
      where: { isActive: true },
      data: { isActive: false }
    });
    
    // Activate requested profile
    const profile = await prisma.profile.update({
      where: { id: req.params.id },
      data: { isActive: true },
      include: {
        profileTools: true,
        profileMcpTools: { include: { mcpTool: true } },
        profileSkills: { include: { skill: true } },
        profileTemplates: { include: { template: true } },
        sandboxes: true
      }
    });
    
    res.json(profile);
  } catch (error) {
    console.error('Error activating profile:', error);
    res.status(500).json({ error: 'Failed to activate profile' });
  }
});

export default router;

