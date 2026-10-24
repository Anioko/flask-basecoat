import ProfileHeader from "./components/profile-header";
import ProfileContent from "./components/profile-content";

export default function Page() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <ProfileHeader />
      <ProfileContent />
    </div>
  );
}
