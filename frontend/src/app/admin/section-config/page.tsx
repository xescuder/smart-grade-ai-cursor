'use client';

import { getAuthHeaders } from "@/lib/utils"

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Trash2, Edit, Plus, Settings, Save, X } from 'lucide-react';

interface SectionConfig {
  id: number;
  name: string;
  markers: string;
  description?: string;
  priority: number;
  is_active: boolean;
  extraction_strategy: string;
  max_characters: number;
  created_at: string;
  updated_at: string;
}

interface ApiClient {
  get: (url: string) => Promise<Response>;
  post: (url: string, data: unknown) => Promise<Response>;
  put: (url: string, data: unknown) => Promise<Response>;
  delete: (url: string) => Promise<Response>;
}

// Simple API client for demo purposes
const apiClient: ApiClient = {
  get: (url: string) => fetch(url, {
    headers: { ...getAuthHeaders() }
  }),
  post: (url: string, data: unknown) => fetch(url, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(data)
  }),
  put: (url: string, data: unknown) => fetch(url, {
    method: 'PUT',
    headers: { 
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(data)
  }),
  delete: (url: string) => fetch(url, {
    method: 'DELETE',
    headers: { ...getAuthHeaders() }
  })
};

export default function SectionConfigAdmin() {
  const [configs, setConfigs] = useState<SectionConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SectionConfig | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    markers: '',
    description: '',
    priority: 1,
    is_active: true,
    extraction_strategy: 'section_to_end',
    max_characters: 4000
  });

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      const response = await apiClient.get('/api/v1/admin/section-configs');
      if (response.ok) {
        const data = await response.json();
        setConfigs(data);
      } else {
        console.error('Failed to fetch configs');
      }
    } catch (error) {
      console.error('Error fetching configs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      let response;
      if (editingConfig) {
        response = await apiClient.put(`/api/v1/admin/section-configs/${editingConfig.id}`, formData);
      } else {
        response = await apiClient.post('/api/v1/admin/section-configs', formData);
      }
      
      if (response.ok) {
        await fetchConfigs();
        setIsDialogOpen(false);
        resetForm();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Error saving configuration');
    }
  };

  const handleEdit = (config: SectionConfig) => {
    setEditingConfig(config);
    setFormData({
      name: config.name,
      markers: config.markers,
      description: config.description || '',
      priority: config.priority,
      is_active: config.is_active,
      extraction_strategy: config.extraction_strategy,
      max_characters: config.max_characters
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this configuration?')) {
      try {
        const response = await apiClient.delete(`/api/v1/admin/section-configs/${id}`);
        if (response.ok) {
          await fetchConfigs();
        } else {
          alert('Error deleting configuration');
        }
      } catch (error) {
        console.error('Error deleting config:', error);
        alert('Error deleting configuration');
      }
    }
  };

  const resetForm = () => {
    setEditingConfig(null);
    setFormData({
      name: '',
      markers: '',
      description: '',
      priority: 1,
      is_active: true,
      extraction_strategy: 'section_to_end',
      max_characters: 4000
    });
  };

  const parseMarkers = (markersString: string) => {
    try {
      return JSON.parse(markersString);
    } catch {
      return [];
    }
  };

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading configurations...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Section Extraction Configuration</h1>
          <p className="text-gray-600 mt-2">
            Configure how the AI extracts content from PDF sections like &quot;Què s&apos;ha de lliurar&quot; and &quot;Descripció&quot;
          </p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Add Configuration
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingConfig ? 'Edit' : 'Create'} Section Configuration
              </DialogTitle>
              <DialogDescription>
                Configure search terms and extraction settings for PDF sections
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="name">Configuration Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., &quot;Què s'ha de lliurar&quot;"
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="markers">Search Markers (JSON Array)</Label>
                <Textarea
                  id="markers"
                  value={formData.markers}
                  onChange={(e) => setFormData({...formData, markers: e.target.value})}
                  placeholder={`["què s'ha de lliurar", "descripció", "deliverables"]`}
                  rows={4}
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  JSON array of search terms to find this section in PDFs
                </p>
              </div>
              
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Description of what this configuration is for"
                  rows={2}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="priority">Priority</Label>
                  <Input
                    id="priority"
                    type="number"
                    value={formData.priority}
                    onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
                    min="1"
                    required
                  />
                  <p className="text-sm text-gray-500">Lower number = higher priority</p>
                </div>
                
                <div>
                  <Label htmlFor="max_characters">Max Characters</Label>
                  <Input
                    id="max_characters"
                    type="number"
                    value={formData.max_characters}
                    onChange={(e) => setFormData({...formData, max_characters: parseInt(e.target.value)})}
                    min="1000"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="extraction_strategy">Extraction Strategy</Label>
                  <Select value={formData.extraction_strategy} onValueChange={(value) => setFormData({...formData, extraction_strategy: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="section_to_end">Section to End</SelectItem>
                      <SelectItem value="section_limited">Section Limited</SelectItem>
                      <SelectItem value="full_document">Full Document</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex items-center space-x-2 mt-6">
                  <Switch
                    id="is_active"
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({...formData, is_active: checked})}
                  />
                  <Label htmlFor="is_active">Active</Label>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
                <Button type="submit">
                  <Save className="h-4 w-4 mr-2" />
                  {editingConfig ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4">
        {configs.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center">
              <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No section configurations found. Create your first one!</p>
            </CardContent>
          </Card>
        ) : (
          configs.map((config) => (
            <Card key={config.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {config.name}
                      {!config.is_active && <span className="text-sm bg-gray-200 px-2 py-1 rounded">Inactive</span>}
                      <span className="text-sm bg-blue-100 px-2 py-1 rounded">Priority {config.priority}</span>
                    </CardTitle>
                    <CardDescription>{config.description}</CardDescription>
                  </div>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm" onClick={() => handleEdit(config)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => handleDelete(config.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold mb-2">Search Markers ({parseMarkers(config.markers).length})</h4>
                    <div className="flex flex-wrap gap-1">
                      {parseMarkers(config.markers).map((marker: string, index: number) => (
                        <span key={index} className="bg-gray-100 px-2 py-1 rounded text-sm">
                          &quot;{marker}&quot;
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Configuration</h4>
                    <p className="text-sm text-gray-600">Strategy: {config.extraction_strategy}</p>
                    <p className="text-sm text-gray-600">Max Characters: {config.max_characters.toLocaleString()}</p>
                    <p className="text-sm text-gray-600">Updated: {new Date(config.updated_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
