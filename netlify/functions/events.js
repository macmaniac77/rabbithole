export const config = { path: '/api/events' };

export default async (req) => {
    try {
        if (req.method !== 'POST') {
            return new Response('Method Not Allowed', { status: 405 });
        }

        const body = await req.json();

        if (!body.event || !body.page) {
            return new Response('Bad Request', { status: 400 });
        }

        console.log('EVENT', JSON.stringify(body));

        const domain = process.env.PLAUSIBLE_DOMAIN;
        await fetch('https://plausible.io/api/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'User-Agent': 'server' },
            body: JSON.stringify({
                name: body.event,
                url: `https://${domain}${body.page}`,
                domain,
                props: body
            })
        });

        return new Response(JSON.stringify({ ok: true }), { status: 200 });
    } catch (err) {
        console.error(err);
        return new Response('Internal Error', { status: 500 });
    }
};
