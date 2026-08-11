import { useEffect, useState, type FormEvent } from "react";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Input } from "../../../components/ui/Input";
import { Spinner } from "../../../components/ui/Spinner";
import { useProfile } from "../hooks/useProfile";
import { useUpdateProfile } from "../hooks/useUpdateProfile";

const GENDER_OPTIONS = [
  { value: "", label: "Prefer not to specify" },
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
] as const;

export function ProfilePage() {
  const { data: profile, isLoading, isError, error, refetch } = useProfile();
  const mutation = useUpdateProfile();
  const [phoneNumber, setPhoneNumber] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [gender, setGender] = useState("");
  const [profilePicture, setProfilePicture] = useState("");
  const [bio, setBio] = useState("");
  const [emergencyName, setEmergencyName] = useState("");
  const [emergencyPhone, setEmergencyPhone] = useState("");

  useEffect(() => {
    if (!profile) return;
    setPhoneNumber(profile.phone_number);
    setDateOfBirth(profile.date_of_birth ?? "");
    setGender(profile.gender);
    setProfilePicture(profile.profile_picture);
    setBio(profile.bio);
    setEmergencyName(profile.emergency_contact.name ?? "");
    setEmergencyPhone(profile.emergency_contact.phone ?? "");
  }, [profile]);

  if (isLoading) {
    return <Spinner label="Loading your profile..." />;
  }

  if (isError) {
    return <ErrorState message={error instanceof Error ? error.message : "Failed to load your profile."} onRetry={refetch} />;
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({
      phone_number: phoneNumber.trim(),
      date_of_birth: dateOfBirth || null,
      gender: gender as "male" | "female" | "other" | "prefer_not_to_say" | "",
      profile_picture: profilePicture.trim(),
      bio: bio.trim(),
      emergency_contact: {
        name: emergencyName.trim(),
        phone: emergencyPhone.trim(),
      },
    });
  }

  return (
    <div className="profile-page">
      <div className="profile-heading">
        <div>
          <span className="section-kicker">Your identity & preferences</span>
          <h1>Profile</h1>
          <p>Keep the details TraVerse can use to make your travel experience feel personal.</p>
        </div>
        {mutation.isSuccess && <span className="profile-success">Profile saved</span>}
      </div>

      {mutation.isError && (
        <ErrorState message={mutation.error instanceof Error ? mutation.error.message : "We couldn't save your profile."} />
      )}

      <form onSubmit={submit} className="profile-grid">
        <Card className="profile-card">
          <div className="profile-card-heading">
            <span>01</span>
            <div><h2>Personal details</h2><p>Information you control and can change at any time.</p></div>
          </div>
          <div className="profile-form-grid">
            <Input label="Phone number" value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} autoComplete="tel" />
            <label className="profile-field">
              <span>Date of birth</span>
              <input type="date" value={dateOfBirth} onChange={(event) => setDateOfBirth(event.target.value)} />
            </label>
            <label className="profile-field">
              <span>Gender</span>
              <select value={gender} onChange={(event) => setGender(event.target.value)}>
                {GENDER_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <Input label="Profile picture URL" type="url" value={profilePicture} onChange={(event) => setProfilePicture(event.target.value)} placeholder="https://..." />
          </div>
          <label className="profile-field">
            <span>Bio</span>
            <textarea value={bio} onChange={(event) => setBio(event.target.value)} maxLength={1000} rows={5} placeholder="Tell TraVerse a little about the traveler behind the trips." />
          </label>
        </Card>

        <Card className="profile-card">
          <div className="profile-card-heading">
            <span>02</span>
            <div><h2>Emergency contact</h2><p>Optional information stored with your protected profile.</p></div>
          </div>
          <div className="profile-form-grid">
            <Input label="Contact name" value={emergencyName} onChange={(event) => setEmergencyName(event.target.value)} autoComplete="name" />
            <Input label="Contact phone" value={emergencyPhone} onChange={(event) => setEmergencyPhone(event.target.value)} autoComplete="tel" />
          </div>
          <div className="profile-note">Your profile endpoint is authenticated and only resolves the currently signed-in user's profile.</div>
        </Card>

        <div className="profile-actions">
          <Button type="submit" isLoading={mutation.isPending} className="profile-save">Save profile</Button>
        </div>
      </form>
    </div>
  );
}
