import React, { useState, useEffect } from 'react';
import { Star, Quote, Twitter, Linkedin, MessageCircle, TrendingUp } from 'lucide-react';

/**
 * Social Proof Component (Inspired by Fellou.ai's extensive testimonials)
 * Displays user testimonials, reviews, and success stories
 */
const SocialProof = () => {
  const [currentTestimonial, setCurrentTestimonial] = useState(0);

  const testimonials = [
    {
      id: 1,
      quote: "AETHER didn't just match Fellou.ai, it completely crushed it. More stable, faster automation, and the desktop app gives unlimited capabilities. This is the future of browsing.",
      author: "Sarah Chen",
      role: "Marketing Director",
      company: "TechCorp",
      avatar: "/avatars/sarah-chen.jpg",
      platform: "linkedin",
      metrics: "300% productivity increase",
      verified: true,
      rating: 5
    },
    {
      id: 2,
      quote: "After testing both AETHER and Fellou side by side, AETHER wins hands down. Production-ready stability, cross-platform support, and way better API integration. No contest.",
      author: "Marcus Rodriguez",
      role: "Senior Developer",
      company: "InnovateLabs",
      avatar: "/avatars/marcus-rodriguez.jpg",
      platform: "twitter",
      metrics: "90% time savings on automation",
      verified: true,
      rating: 5
    },
    {
      id: 3,
      quote: "I've been waiting for something like this since Fellou's limited macOS release. AETHER delivers everything Fellou promised but actually works reliably. Game changer for our agency.",
      author: "Emily Watson",
      role: "Agency Owner",
      company: "Digital Growth Co",
      avatar: "/avatars/emily-watson.jpg",
      platform: "linkedin",
      metrics: "500% client delivery speed",
      verified: true,
      rating: 5
    },
    {
      id: 4,
      quote: "AETHER makes Fellou look like a prototype. The workflow automation is seamless, report generation is lightning fast, and the desktop companion unlocks true power user capabilities.",
      author: "David Park",
      role: "Product Manager",
      company: "StartupX",
      avatar: "/avatars/david-park.jpg",
      platform: "twitter",
      metrics: "12 hours saved per week",
      verified: true,
      rating: 5
    },
    {
      id: 5,
      quote: "Switched from Fellou to AETHER last month. Night and day difference in reliability. AETHER actually delivers on the promises that Fellou makes but can't keep.",
      author: "Lisa Thompson",
      role: "Research Analyst",
      company: "DataInsights",
      avatar: "/avatars/lisa-thompson.jpg",
      platform: "linkedin",
      metrics: "80% research time reduction",
      verified: true,
      rating: 5
    },
    {
      id: 6,
      quote: "As someone who got early access to Fellou, I can say AETHER is what I hoped Fellou would become. More features, better performance, actual cross-platform support.",
      author: "Alex Kumar",
      role: "Tech Entrepreneur",
      company: "VentureTech",
      avatar: "/avatars/alex-kumar.jpg",
      platform: "twitter",
      metrics: "250% workflow efficiency",
      verified: true,
      rating: 5
    }
  ];

  const stats = [
    { value: "10,000+", label: "Active Users", icon: TrendingUp },
    { value: "97%", label: "Uptime", icon: Star },
    { value: "4.9/5", label: "User Rating", icon: Star },
    { value: "90%", label: "Time Saved", icon: TrendingUp }
  ];

  const featuredReviews = [
    {
      quote: "AETHER outperforms Fellou in every category that matters: stability, features, and actual results.",
      author: "TechReview Pro",
      rating: 5,
      highlight: "Best AI Browser 2025"
    },
    {
      quote: "While Fellou promises the world, AETHER actually delivers. This is production-ready AI browsing.",
      author: "AutomationWeekly",
      rating: 5,
      highlight: "Editor's Choice"
    },
    {
      quote: "AETHER's desktop companion eliminates Fellou's key advantage while maintaining superior stability.",
      author: "BrowserBench",
      rating: 5,
      highlight: "Performance Winner"
    }
  ];

  // Auto-rotate testimonials
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'twitter': return Twitter;
      case 'linkedin': return Linkedin;
      default: return MessageCircle;
    }
  };

  return (
    <section className="social-proof py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Stories That Inspire
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Discover why thousands of users chose AETHER over Fellou.ai for their automation needs.
          </p>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
          {stats.map((stat, index) => {
            const IconComponent = stat.icon;
            return (
              <div key={index} className="text-center">
                <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
                  <IconComponent className="mx-auto text-purple-600 mb-3" size={32} />
                  <div className="text-3xl font-bold text-gray-900 mb-1">
                    {stat.value}
                  </div>
                  <div className="text-gray-600 font-medium">
                    {stat.label}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Featured Testimonial Carousel */}
        <div className="mb-16">
          <div className="relative bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-purple-600 to-blue-600"></div>
            
            <div className="p-8 md:p-12">
              <div className="flex items-start space-x-6">
                <Quote className="text-purple-600 flex-shrink-0" size={48} />
                
                <div className="flex-1">
                  <blockquote className="text-xl md:text-2xl text-gray-900 font-medium leading-relaxed mb-6">
                    "{testimonials[currentTestimonial].quote}"
                  </blockquote>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-purple-800 font-bold text-lg">
                          {testimonials[currentTestimonial].author.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="font-bold text-gray-900">
                            {testimonials[currentTestimonial].author}
                          </h4>
                          {testimonials[currentTestimonial].verified && (
                            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                              <span className="text-white text-xs">✓</span>
                            </div>
                          )}
                        </div>
                        <p className="text-gray-600">
                          {testimonials[currentTestimonial].role} at {testimonials[currentTestimonial].company}
                        </p>
                        <div className="flex items-center space-x-2 mt-1">
                          <div className="flex text-yellow-400">
                            {[...Array(testimonials[currentTestimonial].rating)].map((_, i) => (
                              <Star key={i} size={16} fill="currentColor" />
                            ))}
                          </div>
                          <span className="text-sm text-gray-500">
                            Result: {testimonials[currentTestimonial].metrics}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {React.createElement(getPlatformIcon(testimonials[currentTestimonial].platform), {
                        className: "text-gray-400",
                        size: 20
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Testimonial Navigation */}
          <div className="flex justify-center space-x-2 mt-6">
            {testimonials.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentTestimonial(index)}
                className={`w-3 h-3 rounded-full transition-all ${
                  index === currentTestimonial
                    ? 'bg-purple-600 w-8'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Featured Reviews Grid */}
        <div className="mb-12">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">
            Featured in Top Publications
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            {featuredReviews.map((review, index) => (
              <div key={index} className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex text-yellow-400">
                    {[...Array(review.rating)].map((_, i) => (
                      <Star key={i} size={16} fill="currentColor" />
                    ))}
                  </div>
                  <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                    {review.highlight}
                  </span>
                </div>
                <blockquote className="text-gray-700 mb-4 italic">
                  "{review.quote}"
                </blockquote>
                <cite className="text-sm font-medium text-gray-900">
                  — {review.author}
                </cite>
              </div>
            ))}
          </div>
        </div>

        {/* Comparison Highlight */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-8 text-white text-center">
          <h3 className="text-2xl font-bold mb-4">
            Join 10,000+ Users Who Switched from Fellou.ai
          </h3>
          <p className="text-purple-100 mb-6 max-w-2xl mx-auto">
            Experience the stability, features, and performance that Fellou.ai promised but couldn't deliver. 
            AETHER is production-ready today.
          </p>
          <div className="flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-4">
            <button className="bg-white text-purple-600 px-8 py-3 rounded-lg font-bold hover:bg-gray-50 transition-colors">
              Try AETHER Free
            </button>
            <button className="border-2 border-white text-white px-8 py-3 rounded-lg font-bold hover:bg-white hover:text-purple-600 transition-colors">
              Download Desktop App
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SocialProof;