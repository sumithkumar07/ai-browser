import React, { useState } from 'react';
import { Play, ExternalLink, Clock, Users, Zap, BarChart3 } from 'lucide-react';

/**
 * Workflow Gallery Component (Inspired by Fellou.ai's 25+ video examples)
 * Showcases AETHER's automation capabilities with video demonstrations
 */
const WorkflowGallery = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [playingVideo, setPlayingVideo] = useState(null);

  const workflowExamples = [
    {
      id: 1,
      title: "LinkedIn Lead Generation & CRM Integration",
      description: "Extract 50+ qualified leads, analyze profiles, export to Salesforce with contact scoring",
      category: "business",
      duration: "2:30",
      thumbnail: "/images/workflows/linkedin-leads.jpg",
      videoUrl: "/videos/linkedin-automation.mp4",
      tags: ["LinkedIn", "CRM", "Lead Gen"],
      results: "190% increase in qualified leads"
    },
    {
      id: 2,
      title: "Multi-Platform Social Media Campaign",
      description: "Schedule and post content across Twitter, LinkedIn, Facebook with performance tracking",
      category: "marketing",
      duration: "1:45",
      thumbnail: "/images/workflows/social-media.jpg",
      videoUrl: "/videos/social-automation.mp4",
      tags: ["Social Media", "Marketing", "Analytics"],
      results: "300% engagement increase"
    },
    {
      id: 3,
      title: "E-commerce Price Monitoring & Competitor Analysis",
      description: "Track competitor prices across 15+ platforms, send alerts, generate pricing reports",
      category: "analytics",
      duration: "3:15",
      thumbnail: "/images/workflows/price-monitoring.jpg",
      videoUrl: "/videos/price-monitoring.mp4",
      tags: ["E-commerce", "Analytics", "Alerts"],
      results: "25% profit margin improvement"
    },
    {
      id: 4,
      title: "Automated Customer Support Ticket Management",
      description: "Classify tickets, route to specialists, generate response drafts, track resolution",
      category: "business",
      duration: "2:00",
      thumbnail: "/images/workflows/customer-support.jpg",
      videoUrl: "/videos/support-automation.mp4",
      tags: ["Support", "Automation", "AI"],
      results: "60% faster resolution time"
    },
    {
      id: 5,
      title: "Research Report Generation & Data Visualization",
      description: "Gather data from 20+ sources, analyze trends, create interactive reports",
      category: "analytics",
      duration: "4:20",
      thumbnail: "/images/workflows/research-reports.jpg",
      videoUrl: "/videos/research-automation.mp4",
      tags: ["Research", "Reports", "Visualization"],
      results: "90% time savings on research"
    },
    {
      id: 6,
      title: "Real Estate Market Analysis & Lead Nurturing",
      description: "Scrape property listings, analyze market trends, nurture leads through email sequences",
      category: "business",
      duration: "3:45",
      thumbnail: "/images/workflows/real-estate.jpg",
      videoUrl: "/videos/realestate-automation.mp4",
      tags: ["Real Estate", "Analytics", "CRM"],
      results: "150% increase in closings"
    },
    {
      id: 7,
      title: "Automated Job Application & Interview Scheduling",
      description: "Apply to relevant positions, track applications, schedule interviews, follow up",
      category: "productivity",
      duration: "2:15",
      thumbnail: "/images/workflows/job-applications.jpg",
      videoUrl: "/videos/job-automation.mp4",
      tags: ["Jobs", "Scheduling", "Automation"],
      results: "5x more interviews scheduled"
    },
    {
      id: 8,
      title: "Content Creation & SEO Optimization Pipeline",
      description: "Research topics, generate content, optimize for SEO, schedule publishing",
      category: "marketing",
      duration: "3:30",
      thumbnail: "/images/workflows/content-creation.jpg",
      videoUrl: "/videos/content-automation.mp4",
      tags: ["Content", "SEO", "Publishing"],
      results: "400% organic traffic growth"
    },
    {
      id: 9,
      title: "Financial Data Aggregation & Investment Analysis",
      description: "Collect financial data, analyze trends, generate investment recommendations",
      category: "analytics",
      duration: "4:00",
      thumbnail: "/images/workflows/financial-analysis.jpg",
      videoUrl: "/videos/finance-automation.mp4",
      tags: ["Finance", "Investment", "Analysis"],
      results: "23% portfolio performance improvement"
    },
    {
      id: 10,
      title: "Event Management & Attendee Engagement",
      description: "Manage registrations, send communications, track engagement, generate reports",
      category: "business",
      duration: "2:45",
      thumbnail: "/images/workflows/event-management.jpg",
      videoUrl: "/videos/event-automation.mp4",
      tags: ["Events", "Management", "Engagement"],
      results: "80% reduction in manual work"
    },
    {
      id: 11,
      title: "Inventory Management & Supplier Coordination",
      description: "Track inventory levels, automate reordering, coordinate with suppliers",
      category: "business",
      duration: "3:00",
      thumbnail: "/images/workflows/inventory.jpg",
      videoUrl: "/videos/inventory-automation.mp4",
      tags: ["Inventory", "Supply Chain", "Automation"],
      results: "40% reduction in stockouts"
    },
    {
      id: 12,
      title: "Academic Research & Citation Management",
      description: "Search academic databases, organize papers, generate citations, track references",
      category: "productivity",
      duration: "3:20",
      thumbnail: "/images/workflows/academic-research.jpg",
      videoUrl: "/videos/academic-automation.mp4",
      tags: ["Research", "Academic", "Citations"],
      results: "70% faster research process"
    }
  ];

  const categories = [
    { id: 'all', name: 'All Workflows', icon: Zap, count: workflowExamples.length },
    { id: 'business', name: 'Business', icon: BarChart3, count: workflowExamples.filter(w => w.category === 'business').length },
    { id: 'marketing', name: 'Marketing', icon: Users, count: workflowExamples.filter(w => w.category === 'marketing').length },
    { id: 'analytics', name: 'Analytics', icon: BarChart3, count: workflowExamples.filter(w => w.category === 'analytics').length },
    { id: 'productivity', name: 'Productivity', icon: Clock, count: workflowExamples.filter(w => w.category === 'productivity').length }
  ];

  const filteredWorkflows = selectedCategory === 'all' 
    ? workflowExamples 
    : workflowExamples.filter(workflow => workflow.category === selectedCategory);

  const handleVideoPlay = (videoId) => {
    setPlayingVideo(videoId);
  };

  return (
    <section className="workflow-gallery py-16 bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Automate Workflows, Not Headaches
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            From lead generation to market analysis, AETHER automates complex multi-step workflows 
            across 50+ platforms—no coding needed, just intelligent automation.
          </p>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {categories.map((category) => {
            const IconComponent = category.icon;
            return (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`flex items-center space-x-2 px-6 py-3 rounded-full font-medium transition-all duration-300 ${
                  selectedCategory === category.id
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 border border-gray-200 hover:border-purple-300 hover:text-purple-600'
                }`}
              >
                <IconComponent size={18} />
                <span>{category.name}</span>
                <span className="text-sm opacity-75">({category.count})</span>
              </button>
            );
          })}
        </div>

        {/* Workflow Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredWorkflows.map((workflow) => (
            <div 
              key={workflow.id}
              className="bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 overflow-hidden group"
            >
              {/* Video Thumbnail */}
              <div className="relative">
                <div className="aspect-video bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center">
                  {/* Placeholder for video thumbnail */}
                  <div className="w-full h-full bg-gradient-to-br from-purple-200 to-blue-200 flex items-center justify-center relative">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-4 mx-auto shadow-lg">
                        <Play className="text-purple-600" size={24} />
                      </div>
                      <p className="text-purple-800 font-medium">{workflow.title}</p>
                    </div>
                    
                    {/* Video overlay */}
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
                      <button
                        onClick={() => handleVideoPlay(workflow.id)}
                        className="w-20 h-20 bg-white bg-opacity-90 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
                      >
                        <Play className="text-purple-600 ml-1" size={28} />
                      </button>
                    </div>

                    {/* Duration badge */}
                    <div className="absolute bottom-3 right-3 bg-black bg-opacity-75 text-white px-2 py-1 rounded text-sm">
                      {workflow.duration}
                    </div>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
                  {workflow.title}
                </h3>
                <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                  {workflow.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {workflow.tags.map((tag, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 bg-purple-100 text-purple-600 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Results */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="text-green-600" size={16} />
                    <span className="text-green-800 font-medium text-sm">
                      Result: {workflow.results}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3">
                  <button 
                    onClick={() => handleVideoPlay(workflow.id)}
                    className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity flex items-center justify-center space-x-2"
                  >
                    <Play size={16} />
                    <span>Watch Demo</span>
                  </button>
                  <button className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:border-purple-300 hover:text-purple-600 transition-colors">
                    <ExternalLink size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* View All Button */}
        <div className="text-center mt-12">
          <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-4 rounded-lg font-medium text-lg hover:opacity-90 transition-opacity shadow-lg">
            View All {workflowExamples.length}+ Workflows
          </button>
        </div>
      </div>

      {/* Video Modal (placeholder) */}
      {playingVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">
                {workflowExamples.find(w => w.id === playingVideo)?.title}
              </h3>
              <button 
                onClick={() => setPlayingVideo(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">Video player would be implemented here</p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default WorkflowGallery;