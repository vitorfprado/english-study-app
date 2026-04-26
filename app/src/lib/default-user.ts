import { prisma } from "./prisma";

export async function getOrCreateDefaultUser() {
  const existing = await prisma.user.findFirst();
  if (existing) return existing;

  return prisma.user.create({
    data: {
      name: "Vitor",
      email: "vitor@example.local",
      passwordHash: "mvp-no-auth"
    }
  });
}
