/**
 * Bug Creation Page
 *
 * Form for creating new bugs with title, description, priority, severity, and project selection.
 * Implements form validation with error messages and handles submission to backend.
 *
 * Requirements: 1.1, 1.5
 */

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/router";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { bugApi, projectApi } from "@/utils/apiClient";
import { BugPriority, BugSeverity, Project } from "@/utils/types";
import { useUser } from "@/contexts/UserContext";

interface BugFormData {
  title: string;
  description: string;
  projectId: string;
  priority: BugPriority;
  severity: BugSeverity;
}

export default function NewBugPage() {
  const router = useRouter();
  const { currentUser } = useUser();

  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<BugFormData>({
    defaultValues: {
      title: "",
      description: "",
      projectId: "",
      priority: BugPriority.MEDIUM,
      severity: BugSeverity.MAJOR,
    },
  });

  const selectedProjectId = watch("projectId");
  const selectedPriority = watch("priority");
  const selectedSeverity = watch("severity");

  const loadProjects = useCallback(async () => {
    setIsLoadingProjects(true);
    try {
      const projectsData = await projectApi.getAll();
      setProjects(projectsData);
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      setIsLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Pre-select project from query parameter
  useEffect(() => {
    if (router.query.projectId && typeof router.query.projectId === "string") {
      setValue("projectId", router.query.projectId, { shouldValidate: true });
    }
  }, [router.query.projectId, setValue]);

  const onSubmit = async (data: BugFormData) => {
    if (!currentUser) {
      setSubmitError("Please select a user first");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const newBug = await bugApi.create({
        title: data.title,
        description: data.description,
        projectId: data.projectId,
        reportedBy: currentUser._id,
        priority: data.priority,
        severity: data.severity,
      });

      // Navigate to the newly created bug
      router.push(`/bugs/${newBug._id}`);
    } catch (err: any) {
      console.error("Failed to create bug:", err);
      setSubmitError(
        err.response?.data?.detail || "Failed to create bug. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.push("/bugs");
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-3xl mx-auto">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">
                  Please select a user to create a bug
                </p>
                <Button onClick={() => router.push("/")}>Go to Home</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={handleCancel}>
            ← Back
          </Button>
        </div>

        {/* Form card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Create New Bug</CardTitle>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-6">
              {/* Title */}
              <div className="space-y-2">
                <Label htmlFor="title">
                  Title <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="title"
                  placeholder="Brief description of the bug"
                  {...register("title", {
                    required: "Title is required",
                    minLength: {
                      value: 5,
                      message: "Title must be at least 5 characters",
                    },
                    maxLength: {
                      value: 200,
                      message: "Title must not exceed 200 characters",
                    },
                  })}
                  className={errors.title ? "border-destructive" : ""}
                />
                {errors.title && (
                  <p className="text-sm text-destructive">
                    {errors.title.message}
                  </p>
                )}
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description">
                  Description <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="description"
                  placeholder="Detailed description of the bug, including steps to reproduce"
                  rows={6}
                  {...register("description", {
                    required: "Description is required",
                    minLength: {
                      value: 20,
                      message: "Description must be at least 20 characters",
                    },
                  })}
                  className={errors.description ? "border-destructive" : ""}
                />
                {errors.description && (
                  <p className="text-sm text-destructive">
                    {errors.description.message}
                  </p>
                )}
              </div>

              {/* Project selection */}
              <div className="space-y-2">
                <Label htmlFor="projectId">
                  Project <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={selectedProjectId}
                  onValueChange={(value) =>
                    setValue("projectId", value, { shouldValidate: true })
                  }
                  disabled={isLoadingProjects}
                >
                  <SelectTrigger
                    className={errors.projectId ? "border-destructive" : ""}
                  >
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project._id} value={project._id}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <input
                  type="hidden"
                  {...register("projectId", {
                    required: "Project is required",
                  })}
                />
                {errors.projectId && (
                  <p className="text-sm text-destructive">
                    {errors.projectId.message}
                  </p>
                )}
              </div>

              {/* Priority and Severity row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Priority */}
                <div className="space-y-2">
                  <Label htmlFor="priority">
                    Priority <span className="text-destructive">*</span>
                  </Label>
                  <Select
                    value={selectedPriority}
                    onValueChange={(value) =>
                      setValue("priority", value as BugPriority)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={BugPriority.LOW}>
                        {BugPriority.LOW}
                      </SelectItem>
                      <SelectItem value={BugPriority.MEDIUM}>
                        {BugPriority.MEDIUM}
                      </SelectItem>
                      <SelectItem value={BugPriority.HIGH}>
                        {BugPriority.HIGH}
                      </SelectItem>
                      <SelectItem value={BugPriority.CRITICAL}>
                        {BugPriority.CRITICAL}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Severity */}
                <div className="space-y-2">
                  <Label htmlFor="severity">
                    Severity <span className="text-destructive">*</span>
                  </Label>
                  <Select
                    value={selectedSeverity}
                    onValueChange={(value) =>
                      setValue("severity", value as BugSeverity)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={BugSeverity.MINOR}>
                        {BugSeverity.MINOR}
                      </SelectItem>
                      <SelectItem value={BugSeverity.MAJOR}>
                        {BugSeverity.MAJOR}
                      </SelectItem>
                      <SelectItem value={BugSeverity.BLOCKER}>
                        {BugSeverity.BLOCKER}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Reported by (read-only) */}
              <div className="space-y-2">
                <Label>Reported By</Label>
                <Input
                  value={`${currentUser.name} (${currentUser.role})`}
                  disabled
                  className="bg-muted"
                />
              </div>

              {/* Submit error */}
              {submitError && (
                <div className="p-4 bg-destructive/10 border border-destructive rounded-md">
                  <p className="text-sm text-destructive">{submitError}</p>
                </div>
              )}
            </CardContent>

            <CardFooter className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Bug"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
