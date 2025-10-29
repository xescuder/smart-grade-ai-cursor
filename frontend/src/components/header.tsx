/**
 * Sticky Header Component
 * Navigation header with responsive design
 */

"use client"

import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Menu, GraduationCap, User, LogOut } from "lucide-react"


interface HeaderProps {
  user?: {
    name: string
    email: string
    role: "teacher" | "student"
  }
}

export function Header({ user }: HeaderProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  const organizationItems = [
    {
      title: "Courses & Semesters",
      href: "/course-management",
      description: "Create and manage academic courses and their semesters"
    },
    {
      title: "Classrooms & Groups",
      href: "/classroom-management",
      description: "Manage classrooms and their groups"
    }
  ]

  const navigationItems = [
    {
      title: "Assignments",
      href: "/assignment-management",
      description: "Create, edit, and manage assignments with exercises"
    },
    {
      title: "Submissions",
      href: "/submission-management",
      description: "Review and grade student group submissions"
    }
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 flex h-16 items-center">
        {/* Logo */}
        <Link href="/" className="flex items-center space-x-2">
          <GraduationCap className="h-6 w-6" />
          <span className="font-bold">Smart Grade AI</span>
        </Link>

        {/* Desktop Navigation */}
        <NavigationMenu className="hidden md:flex mx-6">
            <NavigationMenuList>
              {/* Organization Dropdown */}
              <NavigationMenuItem>
                <NavigationMenuTrigger>Organization</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                    {organizationItems.map((item) => (
                      <li key={item.href}>
                        <NavigationMenuLink asChild>
                          <a
                            className="block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                            href={item.href}
                          >
                            <div className="text-sm font-medium leading-none">{item.title}</div>
                            <p className="line-clamp-2 text-sm leading-snug text-muted-foreground">
                              {item.description}
                            </p>
                          </a>
                        </NavigationMenuLink>
                      </li>
                    ))}
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>

              {/* Other Navigation Items */}
              {navigationItems.map((item) => (
                <NavigationMenuItem key={item.href}>
                  <NavigationMenuLink asChild>
                    <a
                      className="group inline-flex h-10 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[active]:bg-accent/50 data-[state=open]:bg-accent/50"
                      href={item.href}
                    >
                      {item.title}
                    </a>
                  </NavigationMenuLink>
                </NavigationMenuItem>
              ))}
            </NavigationMenuList>
          </NavigationMenu>

        {/* Right side - User menu or Login */}
        <div className="ml-auto flex items-center space-x-4">
          {user && (
            <>
              {/* User Info */}
              <div className="hidden sm:flex items-center space-x-2">
                <div className="flex items-center space-x-1">
                  <User className="h-4 w-4" />
                  <span className="text-sm font-medium">{user.name}</span>
                </div>
              </div>
              
              {/* Logout Button */}
              <Button variant="outline" size="sm" className="hidden sm:flex">
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </>
          )}

          {/* Mobile Menu */}
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="sm" className="md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <SheetHeader>
                <SheetTitle>Smart Grade AI</SheetTitle>
                <SheetDescription>
                  {user ? `Welcome, ${user.name}` : "Navigation menu"}
                </SheetDescription>
              </SheetHeader>
              <div className="grid gap-4 py-4">
                {mounted && (
                  <>
                    {/* Organization Section */}
                    <div className="grid gap-2">
                      <h4 className="font-medium text-sm text-muted-foreground">Organization</h4>
                      {organizationItems.map((item) => (
                        <Link
                          key={item.href}
                          href={item.href}
                          className="block px-2 py-2 text-sm hover:bg-accent rounded-md"
                          onClick={() => setIsOpen(false)}
                        >
                          <div className="font-medium">{item.title}</div>
                          <div className="text-xs text-muted-foreground">{item.description}</div>
                        </Link>
                      ))}
                    </div>

                    {/* Navigation Section */}
                    <div className="grid gap-2 pt-2 border-t">
                      <h4 className="font-medium text-sm text-muted-foreground">Navigation</h4>
                      {navigationItems.map((item) => (
                        <Link
                          key={item.href}
                          href={item.href}
                          className="block px-2 py-1 text-sm hover:bg-accent rounded-md"
                          onClick={() => setIsOpen(false)}
                        >
                          {item.title}
                        </Link>
                      ))}
                    </div>
                    
                    {user && (
                      <div className="pt-4 border-t">
                        <Button variant="outline" className="w-full">
                          <LogOut className="h-4 w-4 mr-2" />
                          Logout
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
