import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mail,
  Phone,
  MapPin,
  Send,
  Sparkles,
  Facebook,
  Twitter,
  Linkedin,
  Instagram,
  ArrowUp,
  Loader2,
  CheckCircle2,
  Search,
  ShoppingBag,
  ArrowUpRight,
} from "lucide-react";
import { toast } from "sonner";
import { Footer } from "@/components/Footer";

export const Route = createFileRoute("/contact")({
  component: ContactUs,
});

// Framer Motion Animation Constants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 20,
    },
  },
};

function ContactUs() {
  const [formState, setFormState] = useState({
    name: "",
    email: "",
    website: "",
    comment: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [subscribeEmail, setSubscribeEmail] = useState("");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isSubmittingSubscribe, setIsSubmittingSubscribe] = useState(false);

  // Scroll to top functionality
  const [showScrollTop, setShowScrollTop] = useState(false);
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formState.name || !formState.email || !formState.comment) {
      toast.error("Please fill in all required fields.");
      return;
    }

    setIsSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsSubmitting(false);

    toast.success("Thank you for getting in touch! We'll review your inquiry shortly.", {
      description: "Our operational officers have been notified.",
    });

    setFormState({
      name: "",
      email: "",
      website: "",
      comment: "",
    });
  };

  const handleSubscribeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subscribeEmail) return;

    setIsSubmittingSubscribe(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSubmittingSubscribe(false);
    setIsSubscribed(true);
    toast.success("Subscribed successfully to our newsletter!");
    setSubscribeEmail("");
    setTimeout(() => setIsSubscribed(false), 5000);
  };

  return (
    <div className="min-h-screen bg-[#060713] text-white antialiased overflow-x-hidden relative selection:bg-purple-500/30 font-sans">
      {/* Mesh Grid Backdrop */}
      <div className="absolute inset-0 bg-grid opacity-[0.06] pointer-events-none z-0" />

      {/* Cybernetic glowing radial spotlights */}
      <div className="pointer-events-none absolute top-[-10%] left-[-10%] h-[600px] w-[600px] rounded-full bg-[radial-gradient(closest-side,rgba(168,85,247,0.12),transparent)] blur-3xl z-0" />
      <div className="pointer-events-none absolute top-[30%] right-[-10%] h-[700px] w-[700px] rounded-full bg-[radial-gradient(closest-side,rgba(236,72,153,0.08),transparent)] blur-3xl z-0" />
      <div className="pointer-events-none absolute bottom-[10%] left-[10%] h-[650px] w-[650px] rounded-full bg-[radial-gradient(closest-side,rgba(59,130,246,0.08),transparent)] blur-3xl z-0" />

      {/* Top Announcement Strip */}


      {/* Navigation Header */}


      {/* Page Title Hero Section */}
      <section className="relative pt-24 pb-20 flex flex-col items-center justify-center text-center overflow-hidden">
        {/* Massive Purple/Pink Neon Glow behind the header */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-[radial-gradient(closest-side,rgba(168,85,247,0.18),transparent)] blur-3xl z-0" />

        <div className="relative z-10 space-y-4">
          <h1 className="text-5xl md:text-7xl font-black tracking-tight text-white uppercase font-display">
            Contacts
          </h1>
          <div className="flex items-center justify-center gap-2 text-xs font-semibold text-white/50 uppercase tracking-widest font-mono">
            <Link to="/" className="hover:text-white transition-colors">Home</Link>
            <span className="text-white/30">&rsaquo;</span>
            <span className="text-white">Contacts</span>
          </div>
        </div>
      </section>

      {/* Info Section */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        className="max-w-6xl mx-auto px-6 py-20 relative z-10"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">

          {/* Left Column */}
          <motion.div variants={itemVariants} className="lg:col-span-6 space-y-8">
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-[1.5px] bg-[#ec4899] relative flex items-center justify-start">
                  <div className="absolute left-0 w-2 h-2 border-t border-l border-[#ec4899] -rotate-45 -translate-y-[3px]" />
                </div>
                <span className="text-[10px] font-bold text-[#ec4899] tracking-[0.25em] uppercase font-mono">Connect With Us</span>
              </div>
              <h2 className="text-4xl sm:text-5xl md:text-6xl font-black leading-tight text-white tracking-tight font-display">
                Let's Start Work Together. Get in Touch
              </h2>
            </div>

            <motion.a
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
              href="#contact-form"
              className="inline-flex items-center justify-center bg-[#5a24aa] hover:bg-[#6c2ec2] text-white text-xs font-bold px-8 py-4 rounded-full transition-all duration-300 hover:shadow-[0_8px_30px_rgb(90,36,170,0.4)] uppercase tracking-wider"
            >
              Get in Touch
            </motion.a>
          </motion.div>

          {/* Right Column */}
          <motion.div variants={itemVariants} className="lg:col-span-6 space-y-10 lg:pl-6">
            <p className="text-white/60 text-[15px] leading-relaxed">
              Get in touch to discuss your employee wellbeing needs today. Please give us a call, drop us an email, or complete the quick contact form. We are dedicated to providing global support and responsive operations.
            </p>

            {/* Information Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 pt-4">
              <div className="group">
                <h4 className="text-[10px] font-bold text-[#a855f7] tracking-widest uppercase mb-2 font-mono">Address:</h4>
                <p className="text-white/80 text-[14px] leading-relaxed font-medium transition-colors group-hover:text-white">
                  27 Division St, New York,<br />NY 10002, USA
                </p>
              </div>

              <div className="group">
                <h4 className="text-[10px] font-bold text-[#a855f7] tracking-widest uppercase mb-2 font-mono">Phone:</h4>
                <p className="text-white/80 text-[14px] leading-relaxed font-mono font-medium hover:text-[#a855f7] transition-colors">
                  <a href="tel:+1800123456789">+1 800 123 456 789</a>
                </p>
              </div>

              <div className="group">
                <h4 className="text-[10px] font-bold text-[#a855f7] tracking-widest uppercase mb-2 font-mono">Working Hours:</h4>
                <p className="text-white/80 text-[14px] leading-relaxed font-medium transition-colors group-hover:text-white">
                  Mon – Fri: 9 am – 6 pm
                </p>
              </div>

              <div>
                <h4 className="text-[10px] font-bold text-[#a855f7] tracking-widest uppercase mb-2 font-mono">In Socials:</h4>
                <div className="flex items-center gap-4 mt-2">
                  {[
                    { icon: Twitter, href: "https://twitter.com" },
                    { icon: Facebook, href: "https://facebook.com" },
                    { icon: Linkedin, href: "https://linkedin.com" },
                    { icon: Instagram, href: "https://instagram.com" },
                  ].map((soc, i) => (
                    <motion.a
                      key={i}
                      href={soc.href}
                      target="_blank"
                      rel="noreferrer"
                      whileHover={{ y: -3, scale: 1.15 }}
                      className="text-white/50 hover:text-white transition-colors duration-300"
                    >
                      <soc.icon className="h-4.5 w-4.5" />
                      <span className="sr-only">Social Link</span>
                    </motion.a>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>


      </motion.section>

      {/* Grayscale Styled Map Section */}


      {/* Contact Form Section with Rounded Container */}
      <section id="contact-form" className="bg-[#03030c] pt-24 pb-20 rounded-t-[50px] relative z-20 border-t border-white/5">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="max-w-4xl mx-auto px-6 text-center space-y-12"
        >
          {/* Top Star Decoration */}
          <motion.div variants={itemVariants} className="flex justify-center">
            <Sparkles className="h-6 w-6 text-[#ec4899] animate-pulse" />
          </motion.div>

          {/* Heading */}
          <motion.div variants={itemVariants} className="space-y-3">
            <h3 className="text-3xl sm:text-5xl font-black tracking-tight font-display text-white">
              Let's Bring Your Vision Into Reality
            </h3>
            <p className="text-xs text-white/40 tracking-wider font-mono">
              Your email address will not be published. Required fields are marked *
            </p>
          </motion.div>

          {/* Form */}
          <motion.form
            variants={itemVariants}
            onSubmit={handleFormSubmit}
            className="space-y-10 text-left pt-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Name */}
              <div className="relative group/field">
                <input
                  type="text"
                  required
                  placeholder="Your Name *"
                  value={formState.name}
                  onChange={(e) => setFormState({ ...formState, name: e.target.value })}
                  className="w-full bg-transparent border-b border-white/20 focus:border-[#a855f7] py-3.5 text-sm text-white placeholder:text-white/30 outline-none transition-all duration-300"
                />
                <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-[#a855f7] group-focus-within/field:w-full transition-all duration-500" />
              </div>

              {/* Email */}
              <div className="relative group/field">
                <input
                  type="email"
                  required
                  placeholder="Your Email *"
                  value={formState.email}
                  onChange={(e) => setFormState({ ...formState, email: e.target.value })}
                  className="w-full bg-transparent border-b border-white/20 focus:border-[#a855f7] py-3.5 text-sm text-white placeholder:text-white/30 outline-none transition-all duration-300"
                />
                <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-[#a855f7] group-focus-within/field:w-full transition-all duration-500" />
              </div>
            </div>

            {/* Website */}
            <div className="relative group/field">
              <input
                type="url"
                placeholder="Website"
                value={formState.website}
                onChange={(e) => setFormState({ ...formState, website: e.target.value })}
                className="w-full bg-transparent border-b border-white/20 focus:border-[#a855f7] py-3.5 text-sm text-white placeholder:text-white/30 outline-none transition-all duration-300"
              />
              <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-[#a855f7] group-focus-within/field:w-full transition-all duration-500" />
            </div>

            {/* Comment */}
            <div className="relative group/field">
              <textarea
                required
                rows={5}
                placeholder="Your Comment *"
                value={formState.comment}
                onChange={(e) => setFormState({ ...formState, comment: e.target.value })}
                className="w-full bg-transparent border-b border-white/20 focus:border-[#a855f7] py-3 text-sm text-white placeholder:text-white/30 outline-none transition-all duration-300 resize-none"
              />
              <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-[#a855f7] group-focus-within/field:w-full transition-all duration-500" />
            </div>

            {/* Submit */}
            <div className="flex justify-center pt-4">
              <motion.button
                type="submit"
                disabled={isSubmitting}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.98 }}
                className="group relative inline-flex items-center justify-center gap-2 overflow-hidden bg-[#5a24aa] hover:bg-[#6c2ec2] text-white text-xs font-bold px-10 py-4.5 rounded-full transition-all duration-300 hover:shadow-[0_10px_35px_-8px_rgba(90,36,170,0.6)] cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4.5 w-4.5 animate-spin" />
                    <span>Transmitting...</span>
                  </>
                ) : (
                  <>
                    <span>Get in Touch</span>
                    <Send className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                  </>
                )}
              </motion.button>
            </div>
          </motion.form>
        </motion.div>
      </section>

      <Footer />

      {/* Floating scroll to top button */}
      <AnimatePresence>
        {showScrollTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            onClick={scrollToTop}
            className="fixed bottom-6 right-6 z-50 bg-[#5a24aa] hover:bg-[#6c2ec2] text-white p-3.5 rounded-full shadow-2xl cursor-pointer hover:shadow-[0_8px_25px_rgb(90,36,170,0.5)] transition-all duration-300"
            aria-label="Back to top"
          >
            <ArrowUp className="h-4.5 w-4.5" />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
