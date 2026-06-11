import dotenv from "dotenv";
dotenv.config();

import passport from "passport";
import { Strategy as GoogleStrategy } from "passport-google-oauth20";

import User from "../modules/auth/auth.model.js";



passport.use(
  new GoogleStrategy(
    {
      clientID: process.env.GOOGLE_CLIENT_ID,

      clientSecret:
        process.env.GOOGLE_CLIENT_SECRET,

      callbackURL:
        "http://localhost:5000/api/auth/google/callback"
    },

    async (
      accessToken,
      refreshToken,
      profile,
      done
    ) => {

      try {

        // ===============================
        // Extract Google profile data
        // ===============================

        const email = profile.emails[0].value;

        const name = profile.displayName;

        const avatar = profile.photos[0].value;

        const googleId = profile.id;


        // ===============================
        // Check if user already exists
        // ===============================

        let user = await User.findOne({
          email
        });


        // ===============================
        // Existing User
        // ===============================

        if (user) {

          // Attach Google account if missing
          if (!user.googleId) {

            user.googleId = googleId;

            user.avatar = avatar;

            user.provider = "google";

            await user.save();
          }

          return done(null, user);
        }


        // ===============================
        // Generate username automatically
        // ===============================

        const randomNum = Math.floor(
          1000 + Math.random() * 9000
        );

        const generatedUsername =
          email.split("@")[0] +
          "_" +
          randomNum;


        // ===============================
        // Create new Google user
        // ===============================

        user = await User.create({

          name,

          email,

          username: generatedUsername,

          googleId,

          avatar,

          provider: "google"

        });


        done(null, user);

      } catch (error) {

        done(error, null);

      }
    }
  )
);