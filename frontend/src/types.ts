export interface User {
  id: number
  email: string
  name: string
  date_joined: string
}

export interface Event {
  id: number
  name: string
  date_text: string
  venue: string
  dress_code: string
  rsvp_contacts: string[]
  card_bg_color: string
  card_text_color: string
  card_accent_color: string
  artwork: string | null
  artwork_crop: Record<string, number>
  message_template: string
  created_at: string
  my_role: 'owner' | 'manager' | 'scanner'
  guest_count: number
}

export interface Member {
  id: number
  email: string
  name: string
  role: 'manager' | 'scanner'
  invited_email: string
}

export interface Guest {
  id: number
  uuid: string
  title: string
  name: string
  phone: string
  phones: string[]
  admits: number
  rsvp_status: 'pending' | 'attending' | 'declined'
  rsvp_count: number
  rsvp_at: string | null
  attended: boolean
  attended_at: string | null
  pdf_path: string
  created_at: string
}

export interface SmsLog {
  id: number
  guest: number
  guest_name: string
  phone: string
  kind: 'invite' | 'otp'
  status: string
  api_response: string
  sent_at: string
}

export interface PublicEvite {
  uuid: string
  title: string
  name: string
  admits: number
  rsvp_status: string
  rsvp_count: number
  attended: boolean
  has_phone: boolean
  can_admit: boolean
  event: {
    id: number
    name: string
    date_text: string
    venue: string
    dress_code: string
  }
}

export interface GenStatus {
  status: 'none' | 'queued' | 'running' | 'done' | 'failed'
  total: number
  done: number
  error?: string
}
