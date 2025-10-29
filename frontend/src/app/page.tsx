/**
 * Smart Grade AI - Home Page
 * Landing page showcasing the AI-powered grading system
 */

import { Button } from "@/components/ui/button"
import { GraduationCap, Brain, Clock, TrendingUp, Users, FileText } from "lucide-react"
import Link from "next/link"

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-20 px-6">
        <div className="container mx-auto max-w-4xl text-center">
          <div className="flex justify-center mb-6">
            <div className="bg-white p-3 rounded-full shadow-lg">
              <GraduationCap className="h-12 w-12 text-blue-600" />
            </div>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Smart Grade AI
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Revolutionize education with AI-powered assignment grading. 
            Save time, provide consistent feedback, and enhance learning outcomes.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild className="text-lg px-8 py-4">
              <Link href="/dashboard">Get Started</Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="text-lg px-8 py-4">
              <Link href="/demo">Watch Demo</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Powerful AI Grading Features
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Experience the future of education with our comprehensive AI-powered grading system
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* AI Grading */}
            <div className="bg-white p-6 rounded-lg shadow-lg border">
              <div className="bg-blue-100 p-3 rounded-full w-fit mb-4">
                <Brain className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI-Powered Grading</h3>
              <p className="text-gray-600">
                Advanced AI models provide accurate, consistent grading with detailed feedback 
                based on your custom rubrics and criteria.
              </p>
            </div>

            {/* Time Saving */}
            <div className="bg-white p-6 rounded-lg shadow-lg border">
              <div className="bg-green-100 p-3 rounded-full w-fit mb-4">
                <Clock className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Save Time</h3>
              <p className="text-gray-600">
                Reduce grading time by up to 90%. Focus on teaching while AI handles 
                the repetitive grading tasks with remarkable accuracy.
              </p>
            </div>

            {/* Analytics */}
            <div className="bg-white p-6 rounded-lg shadow-lg border">
              <div className="bg-purple-100 p-3 rounded-full w-fit mb-4">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Smart Analytics</h3>
              <p className="text-gray-600">
                Gain insights into student performance, identify learning gaps, 
                and track progress with comprehensive analytics dashboards.
              </p>
            </div>

            {/* Student Management */}
            <div className="bg-white p-6 rounded-lg shadow-lg border">
              <div className="bg-orange-100 p-3 rounded-full w-fit mb-4">
                <Users className="h-6 w-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Student Management</h3>
              <p className="text-gray-600">
                Easily manage students, assignments, and submissions with an 
                intuitive interface designed for educators.
              </p>
            </div>

            {/* Multiple Formats */}
            <div className="bg-white p-6 rounded-lg shadow-lg border">
              <div className="bg-red-100 p-3 rounded-full w-fit mb-4">
                <FileText className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Multiple Formats</h3>
              <p className="text-gray-600">
                Support for various file formats including PDF, DOCX, and plain text. 
                Handle essays, reports, and other written assignments.
              </p>
            </div>

            {/* Custom Rubrics */}
            <div className="bg-white p-6 rounded-lg shadow-lg border">
              <div className="bg-indigo-100 p-3 rounded-full w-fit mb-4">
                <GraduationCap className="h-6 w-6 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Custom Rubrics</h3>
              <p className="text-gray-600">
                Create detailed grading rubrics that align with your teaching objectives. 
                AI adapts to your specific grading criteria and standards.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gray-900 text-white py-20 px-6">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Transform Your Grading Process?
          </h2>
          <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto">
            Join thousands of educators who have already revolutionized their 
            teaching with Smart Grade AI.
          </p>
          <Button size="lg" asChild className="text-lg px-8 py-4">
            <Link href="/register">Start Free Trial</Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 py-12 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <GraduationCap className="h-6 w-6" />
              <span className="font-bold text-lg">Smart Grade AI</span>
            </div>
            <div className="flex space-x-6 text-sm text-gray-600">
              <Link href="/privacy" className="hover:text-gray-900">Privacy Policy</Link>
              <Link href="/terms" className="hover:text-gray-900">Terms of Service</Link>
              <Link href="/support" className="hover:text-gray-900">Support</Link>
            </div>
          </div>
          <div className="border-t border-gray-200 mt-8 pt-8 text-center text-sm text-gray-600">
            © 2024 Smart Grade AI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}