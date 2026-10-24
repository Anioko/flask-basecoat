import * as React from "react";
import { Html, Button, Text, Container } from "@react-email/components";

export default function EmailSubscribeForm() {
  return (
    <Html lang="en">
      <Container style={{ backgroundColor: "#000000", paddingLeft: 12, paddingRight: 12 }}>
        <Text
          style={{ color: "rgb(129,140,248)", fontSize: 24, lineHeight: "32px", fontWeight: 600 }}>
          Congratulations! You are now on our Email List 🎉
        </Text>
        <Text style={{ color: "rgb(255,255,255)", paddingLeft: 12, paddingRight: 12 }}>
          We are so excited that you have joined us! Now you&#39;ll be the first to know about the
          latest updates, brand new features, beautiful templates and special offers.
        </Text>
        <Text style={{ color: "rgb(255,255,255)", paddingLeft: 12, paddingRight: 12 }}>
          Plus, we have some special surprises for you! Stay tuned, we&#39;ll be back with great
          deals very soon.
        </Text>
        <Text style={{ color: "rgb(255,255,255)", paddingLeft: 12, paddingRight: 12 }}>
          Thank you and a pleasant journey awaits us! 🚀
        </Text>
        <Button
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: 12,
            fontWeight: 600,
            borderRadius: 8,
            textAlign: "center",
            backgroundColor: "rgb(79,70,229)",
            color: "rgb(255,255,255)",
            marginBottom: 12
          }}
          href={process.env.BASE_URL}>
          Go to Shadcn UI Kit
        </Button>
      </Container>
    </Html>
  );
}
