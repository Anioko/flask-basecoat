import { CourseHeader } from "./components/course-header";
import { VideoPlayer } from "./components/video-player";
import { CourseCurriculum } from "./components/course-curriculum";
import { CourseDetails } from "./components/course-details";
import { InstructorProfile } from "./components/instructor-profile";

export default function CoursePage() {
  return (
    <div>
      <CourseHeader />

      <main className="px-4 py-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="space-y-8 lg:col-span-2">
            <VideoPlayer />
            <CourseDetails />
            <InstructorProfile />
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <CourseCurriculum />
          </div>
        </div>
      </main>
    </div>
  );
}
