import React, { useState } from 'react';
import { BarChart3, TrendingUp, FileText, ExternalLink, Download, Eye } from 'lucide-react';

/**
 * Report Showcase Component (Inspired by Fellou.ai's report examples)
 * Displays generated reports with visual previews and real data examples
 */
const ReportShowcase = () => {
  const [selectedReport, setSelectedReport] = useState(null);

  const reportExamples = [
    {
      id: 1,
      title: "Comprehensive Market Analysis: AI Browser Competition",
      description: "Deep analysis of 15+ AI browser competitors with market positioning, features, and growth trajectories",
      category: "Market Research",
      preview: "/images/reports/market-analysis-preview.jpg",
      metrics: {
        dataPoints: "500+",
        sources: "25",
        timeToGenerate: "8 minutes"
      },
      highlights: [
        "Fellou.ai vs AETHER competitive matrix",
        "Market size: $2.3B by 2025",
        "Key growth drivers identified",
        "Investment opportunities ranked"
      ],
      colors: ["#6366F1", "#8B5CF6"],
      icon: BarChart3
    },
    {
      id: 2,
      title: "LinkedIn Lead Generation Performance Report",
      description: "Qualified lead analysis with contact scoring, industry breakdown, and engagement metrics",
      category: "Lead Generation",
      preview: "/images/reports/linkedin-leads-preview.jpg",
      metrics: {
        dataPoints: "1,200+",
        sources: "5",
        timeToGenerate: "3 minutes"
      },
      highlights: [
        "190% increase in qualified leads",
        "Top 3 industries: SaaS, FinTech, Healthcare",
        "Optimal outreach timing identified",
        "Response rate: 34% (industry avg: 12%)"
      ],
      colors: ["#0EA5E9", "#06B6D4"],
      icon: TrendingUp
    },
    {
      id: 3,
      title: "E-commerce Price Intelligence Dashboard",
      description: "Real-time competitor pricing analysis across 20+ platforms with profit optimization recommendations",
      category: "Price Analysis",
      preview: "/images/reports/price-intelligence-preview.jpg",
      metrics: {
        dataPoints: "2,500+",
        sources: "20",
        timeToGenerate: "5 minutes"
      },
      highlights: [
        "25% profit margin improvement identified",
        "Dynamic pricing strategy recommended",
        "Competitor gap analysis",
        "Seasonal trend predictions"
      ],
      colors: ["#10B981", "#059669"],
      icon: FileText
    },
    {
      id: 4,
      title: "Social Media Performance Analytics",
      description: "Cross-platform engagement analysis with content optimization and audience insights",
      category: "Social Media",
      preview: "/images/reports/social-analytics-preview.jpg",
      metrics: {
        dataPoints: "3,000+",
        sources: "8",
        timeToGenerate: "4 minutes"
      },
      highlights: [
        "300% engagement rate improvement",
        "Best posting times identified",
        "Content type performance ranking",
        "Audience demographic insights"
      ],
      colors: ["#F59E0B", "#D97706"],
      icon: TrendingUp
    },
    {
      id: 5,
      title: "Investment Opportunity Assessment: EdTech Startups",
      description: "Comprehensive analysis of 50+ EdTech startups with funding, traction, and market fit evaluation",
      category: "Investment Research",
      preview: "/images/reports/edtech-investment-preview.jpg",
      metrics: {
        dataPoints: "800+",
        sources: "15",
        timeToGenerate: "12 minutes"
      },
      highlights: [
        "Top 10 startups ranked by potential",
        "Funding trends and valuations",
        "Market size: $377B by 2028",
        "Exit strategy recommendations"
      ],
      colors: ["#8B5CF6", "#7C3AED"],
      icon: BarChart3
    },
    {
      id: 6,
      title: "Customer Satisfaction & Support Analytics",
      description: "Multi-channel support performance with sentiment analysis and improvement recommendations",
      category: "Customer Analytics",
      preview: "/images/reports/customer-satisfaction-preview.jpg",
      metrics: {
        dataPoints: "1,500+",
        sources: "6",
        timeToGenerate: "6 minutes"
      },
      highlights: [
        "Customer satisfaction: 94% (up from 78%)",
        "Average resolution time: 2.3 hours",
        "Top issues and solutions identified",
        "Agent performance benchmarks"
      ],
      colors: ["#EF4444", "#DC2626"],
      icon: FileText
    }
  ];

  const categories = [
    "All Reports",
    "Market Research", 
    "Lead Generation",
    "Price Analysis",
    "Social Media",
    "Investment Research",
    "Customer Analytics"
  ];

  const [selectedCategory, setSelectedCategory] = useState("All Reports");

  const filteredReports = selectedCategory === "All Reports" 
    ? reportExamples 
    : reportExamples.filter(report => report.category === selectedCategory);

  return (
    <section className="report-showcase py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Transform Data into Decisions: AI-Driven Reports in Seconds
          </h2>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto">
            AETHER's advanced AI analyzes public and private data across platforms to generate 
            actionable reports with visual insights—cutting research time by 90%.
          </p>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-6 py-2 rounded-full font-medium transition-all duration-300 ${
                selectedCategory === category
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* Reports Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredReports.map((report) => {
            const IconComponent = report.icon;
            return (
              <div 
                key={report.id}
                className="bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 overflow-hidden border border-gray-100 group"
              >
                {/* Report Preview */}
                <div className="relative">
                  <div 
                    className="h-48 bg-gradient-to-br flex items-center justify-center relative overflow-hidden"
                    style={{
                      background: `linear-gradient(135deg, ${report.colors[0]}, ${report.colors[1]})`
                    }}
                  >
                    {/* Mock chart/data visualization */}
                    <div className="absolute inset-0 p-6">
                      <div className="bg-white bg-opacity-90 rounded-lg p-4 h-full flex flex-col">
                        <div className="flex items-center justify-between mb-3">
                          <IconComponent className="text-gray-700" size={24} />
                          <span className="text-xs text-gray-500 font-medium">
                            {report.category}
                          </span>
                        </div>
                        
                        {/* Mock chart bars */}
                        <div className="flex-1 flex items-end space-x-2">
                          {[...Array(8)].map((_, i) => (
                            <div 
                              key={i}
                              className="flex-1 rounded-t"
                              style={{
                                height: `${Math.random() * 60 + 20}%`,
                                background: `linear-gradient(to top, ${report.colors[0]}, ${report.colors[1]})`
                              }}
                            />
                          ))}
                        </div>
                        
                        {/* Mock metrics */}
                        <div className="mt-3 text-xs text-gray-600">
                          <div className="flex justify-between">
                            <span>Growth: +{Math.floor(Math.random() * 200 + 50)}%</span>
                            <span>Accuracy: {Math.floor(Math.random() * 10 + 90)}%</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Hover overlay */}
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
                      <button
                        onClick={() => setSelectedReport(report)}
                        className="bg-white bg-opacity-90 text-gray-900 px-4 py-2 rounded-lg font-medium opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-105 flex items-center space-x-2"
                      >
                        <Eye size={16} />
                        <span>View Report</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
                    {report.title}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {report.description}
                  </p>

                  {/* Metrics */}
                  <div className="grid grid-cols-3 gap-4 mb-4 text-center">
                    <div className="bg-gray-50 rounded-lg p-2">
                      <div className="text-lg font-bold text-purple-600">
                        {report.metrics.dataPoints}
                      </div>
                      <div className="text-xs text-gray-500">Data Points</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2">
                      <div className="text-lg font-bold text-blue-600">
                        {report.metrics.sources}
                      </div>
                      <div className="text-xs text-gray-500">Sources</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-2">
                      <div className="text-lg font-bold text-green-600">
                        {report.metrics.timeToGenerate}
                      </div>
                      <div className="text-xs text-gray-500">Generated</div>
                    </div>
                  </div>

                  {/* Key Highlights */}
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Key Insights:</h4>
                    <ul className="space-y-1">
                      {report.highlights.slice(0, 2).map((highlight, index) => (
                        <li key={index} className="text-xs text-gray-600 flex items-start">
                          <span className="text-green-500 mr-2">•</span>
                          {highlight}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => setSelectedReport(report)}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity flex items-center justify-center space-x-2"
                    >
                      <Eye size={16} />
                      <span>View</span>
                    </button>
                    <button className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:border-purple-300 hover:text-purple-600 transition-colors">
                      <Download size={16} />
                    </button>
                    <button className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:border-purple-300 hover:text-purple-600 transition-colors">
                      <ExternalLink size={16} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* View All Button */}
        <div className="text-center mt-12">
          <button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-4 rounded-lg font-medium text-lg hover:opacity-90 transition-opacity shadow-lg">
            Explore All Report Types
          </button>
        </div>
      </div>

      {/* Report Detail Modal */}
      {selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {selectedReport.title}
                  </h3>
                  <p className="text-gray-600">{selectedReport.description}</p>
                </div>
                <button 
                  onClick={() => setSelectedReport(null)}
                  className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              {/* Full highlights */}
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Complete Analysis:</h4>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {selectedReport.highlights.map((highlight, index) => (
                    <li key={index} className="text-sm text-gray-700 flex items-start bg-gray-50 p-3 rounded-lg">
                      <span className="text-green-500 mr-2 mt-1">✓</span>
                      {highlight}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Mock report preview */}
              <div className="bg-gray-100 rounded-lg p-8 text-center mb-6">
                <p className="text-gray-500 mb-4">Interactive Report Preview</p>
                <div 
                  className="h-64 rounded-lg flex items-center justify-center text-white text-xl font-bold"
                  style={{
                    background: `linear-gradient(135deg, ${selectedReport.colors[0]}, ${selectedReport.colors[1]})`
                  }}
                >
                  {selectedReport.title}
                </div>
              </div>

              <div className="flex space-x-4">
                <button className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity">
                  Generate Similar Report
                </button>
                <button className="px-6 py-3 border border-gray-200 text-gray-700 rounded-lg font-medium hover:border-purple-300 hover:text-purple-600 transition-colors">
                  Download PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default ReportShowcase;