import Stripe from 'stripe';

export const config = { path: '/api/stripe/webhook' };

export default async (req) => {
    if (req.method !== 'POST') {
        return new Response('Method Not Allowed', { status: 405 });
    }

    const sig = req.headers.get('stripe-signature');
    const rawBody = await req.text();
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, { apiVersion: '2024-06-20' });

    let event;
    try {
        event = stripe.webhooks.constructEvent(rawBody, sig, process.env.STRIPE_WEBHOOK_SECRET);
    } catch (err) {
        console.error('⚠️  Signature verification failed.', err.message);
        return new Response('Bad Signature', { status: 400 });
    }

    if (event.type === 'checkout.session.completed') {
        const session = event.data.object;
        console.log('REVENUE', JSON.stringify({
            offer_id: session.metadata?.offer_id || 'unknown',
            amount_total: session.amount_total,
            currency: session.currency,
            customer_email: session.customer_details?.email || null
        }));
    }

    return new Response(JSON.stringify({ received: true }), { status: 200 });
};
