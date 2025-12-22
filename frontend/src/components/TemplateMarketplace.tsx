/**
 * TemplateMarketplace Component
 * Browse, search, and use workflow templates
 */

import { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Star,
  Download,
  Play,
  Eye,
  Grid,
  List,
  TrendingUp,
  Clock,
  Tag,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { databaseApi } from '@/services/databaseApi';
import type { Template, TemplateFilters } from '@/types/database';

// ============================================================================
// Types
// ============================================================================

type ViewMode = 'grid' | 'list';
type SortBy = 'downloads' | 'rating' | 'recent';

interface TemplateCardProps {
  template: Template;
  viewMode: ViewMode;
  onUse: (template: Template) => void;
  onPreview: (template: Template) => void;
}

// ============================================================================
// Template Card Component
// ============================================================================

function TemplateCard({ template, viewMode, onUse, onPreview }: TemplateCardProps) {
  const [rating, setRating] = useState<number>(0);

  async function handleRate(stars: number) {
    try {
      await databaseApi.templates.rate(template.id, stars);
      setRating(stars);
      toast.success(`Rated ${stars} stars`);
    } catch (error: any) {
      toast.error('Failed to rate template');
    }
  }

  if (viewMode === 'list') {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div className="flex items-start gap-4">
          <div className="flex-1">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{template.name}</h3>
                {template.category && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded mt-1">
                    <Tag className="w-3 h-3" />
                    {template.category}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <Download className="w-4 h-4" />
                  {template.downloads}
                </div>
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  {template.rating.toFixed(1)}
                </div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {template.description || 'No description available'}
            </p>

            <div className="flex items-center gap-2">
              <button
                onClick={() => onUse(template)}
                className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
              >
                <Play className="w-4 h-4" />
                Use Template
              </button>
              <button
                onClick={() => onPreview(template)}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200 transition-colors"
              >
                <Eye className="w-4 h-4" />
                Preview
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Grid view
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
          {template.name}
        </h3>
        <div className="flex items-center gap-1 text-sm">
          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
          <span className="font-medium">{template.rating.toFixed(1)}</span>
        </div>
      </div>

      {template.category && (
        <div className="mb-2">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
            <Tag className="w-3 h-3" />
            {template.category}
          </span>
        </div>
      )}

      <p className="text-sm text-gray-600 mb-4 line-clamp-3">
        {template.description || 'No description available'}
      </p>

      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <div className="flex items-center gap-1">
          <Download className="w-4 h-4" />
          {template.downloads} uses
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          {new Date(template.created_at).toLocaleDateString()}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <button
          onClick={() => onUse(template)}
          className="flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors w-full"
        >
          <Play className="w-4 h-4" />
          Use Template
        </button>
        <button
          onClick={() => onPreview(template)}
          className="flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200 transition-colors w-full"
        >
          <Eye className="w-4 h-4" />
          Preview
        </button>
      </div>

      {/* Rating */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-center gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => handleRate(star)}
              className="p-1 hover:scale-110 transition-transform"
            >
              <Star
                className={`w-4 h-4 ${
                  star <= (rating || template.rating)
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-300'
                }`}
              />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function TemplateMarketplace() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState<SortBy>('rating');
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);

  // Available categories
  const categories = [
    'All',
    'Data Processing',
    'Code Analysis',
    'Testing',
    'Deployment',
    'Documentation',
    'Security',
    'Monitoring',
  ];

  // Load templates
  useEffect(() => {
    loadTemplates();
  }, [searchQuery, selectedCategory, sortBy]);

  async function loadTemplates() {
    try {
      setLoading(true);
      const filters: TemplateFilters = {
        page: 1,
        limit: 50,
        sort_by: sortBy === 'downloads' ? 'downloads' : sortBy === 'rating' ? 'rating' : 'created_at',
        sort_order: 'desc',
      };

      if (searchQuery) {
        filters.name_contains = searchQuery;
      }

      if (selectedCategory && selectedCategory !== 'All') {
        filters.category = selectedCategory;
      }

      const response = await databaseApi.templates.list(filters);
      setTemplates(response.data);
    } catch (error: any) {
      console.error('Failed to load templates:', error);
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  }

  async function handleUseTemplate(template: Template) {
    try {
      const workflowName = prompt('Enter a name for your new workflow:', template.name);
      if (!workflowName) return;

      await databaseApi.templates.useTemplate(template.id, workflowName);
      toast.success(`Created workflow: ${workflowName}`);
    } catch (error: any) {
      console.error('Failed to use template:', error);
      toast.error('Failed to create workflow from template');
    }
  }

  function handlePreview(template: Template) {
    setPreviewTemplate(template);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Template Marketplace</h2>
        <p className="text-sm text-gray-600">
          Browse and use pre-built workflow templates
        </p>
      </div>

      {/* Search & Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[250px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search templates..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat === 'All' ? '' : cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-gray-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortBy)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="rating">Top Rated</option>
              <option value="downloads">Most Popular</option>
              <option value="recent">Recently Added</option>
            </select>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-1 border border-gray-300 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded ${
                viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'
              }`}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded ${
                viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Templates Grid/List */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          Loading templates...
        </div>
      ) : templates.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600">No templates found</p>
          <p className="text-sm text-gray-500 mt-1">
            Try adjusting your search or filters
          </p>
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
              : 'space-y-3'
          }
        >
          {templates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              viewMode={viewMode}
              onUse={handleUseTemplate}
              onPreview={handlePreview}
            />
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[80vh] overflow-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">
                    {previewTemplate.name}
                  </h3>
                  {previewTemplate.category && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded mt-2">
                      <Tag className="w-3 h-3" />
                      {previewTemplate.category}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setPreviewTemplate(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              <p className="text-gray-600 mb-6">
                {previewTemplate.description}
              </p>

              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-gray-900 mb-2">Workflow Structure</h4>
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(previewTemplate.definition, null, 2)}
                </pre>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    {previewTemplate.downloads} uses
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    {previewTemplate.rating.toFixed(1)} rating
                  </div>
                </div>
                <button
                  onClick={() => {
                    handleUseTemplate(previewTemplate);
                    setPreviewTemplate(null);
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Play className="w-4 h-4" />
                  Use Template
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

